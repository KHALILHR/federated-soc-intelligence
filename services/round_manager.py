"""
Round Manager
Orchestrates federated learning rounds: initiates training on nodes,
collects gradient updates, triggers aggregation, and updates the database.

In production, each step would be a Celery task or an async job
coordinated via Redis. The Django views poll the DB for status.
"""

import logging
from typing import List
from django.utils import timezone
from django.conf import settings

from federated.models import (
    FederatedNode, TrainingRound, GradientUpdate,
    AggregationLog, PrivacyBudget,
)
from threat_detection.models import ThreatModel
from services.fl_engine import FederatedClient, LocalTrainingResult
from services.aggregator import Aggregator, NodeUpdate

logger = logging.getLogger(__name__)


class RoundManager:
    """
    High-level coordinator for a single federated learning round.
    """

    def __init__(self, strategy: str = 'fedavg'):
        self.aggregator = Aggregator(strategy=strategy)

    def create_round(self) -> TrainingRound:
        """Create and persist a new training round."""
        last = TrainingRound.objects.order_by('-round_number').first()
        next_number = (last.round_number + 1) if last else 1

        training_round = TrainingRound.objects.create(
            round_number=next_number,
            status=TrainingRound.Status.SCHEDULED,
            aggregation_strategy=self.aggregator.strategy,
            min_nodes_required=getattr(settings, 'FL_MIN_NODES', 2),
        )

        online_nodes = FederatedNode.objects.filter(status=FederatedNode.Status.ONLINE)
        training_round.participating_nodes.set(online_nodes)

        logger.info("Created Round %d with %d participating nodes",
                     next_number, online_nodes.count())
        return training_round

    def execute_round(self, training_round: TrainingRound) -> bool:
        """
        Execute the full lifecycle of a training round.
        Returns True if the round completed successfully.
        """
        training_round.status = TrainingRound.Status.IN_PROGRESS
        training_round.started_at = timezone.now()
        training_round.save()

        nodes = training_round.participating_nodes.all()
        if nodes.count() < training_round.min_nodes_required:
            training_round.status = TrainingRound.Status.FAILED
            training_round.save()
            logger.warning("Round %d failed: insufficient nodes", training_round.round_number)
            return False

        # Phase 1 — Local training on each node
        results: List[LocalTrainingResult] = []
        for node in nodes:
            client = FederatedClient(
                node_id=str(node.id),
                aggregator_host=getattr(settings, 'AGGREGATOR_HOST', 'localhost'),
                aggregator_port=getattr(settings, 'AGGREGATOR_PORT', 8081),
            )
            client.fetch_global_model()
            result = client.train_local_round(
                round_number=training_round.round_number,
                noise_multiplier=self._get_noise_multiplier(node),
            )
            results.append(result)

            GradientUpdate.objects.create(
                training_round=training_round,
                node=node,
                local_accuracy=result.accuracy,
                local_loss=result.loss,
                num_samples=result.num_samples,
                update_path=result.update_hash,
                epsilon_spent=result.epsilon_spent,
                accepted=True,
            )
            self._consume_budget(node, result.epsilon_spent)

        # Phase 2 — Aggregation
        training_round.status = TrainingRound.Status.AGGREGATING
        training_round.save()

        node_updates = [
            NodeUpdate(
                node_id=r.node_id,
                num_samples=r.num_samples,
                accuracy=r.accuracy,
                loss=r.loss,
                update_hash=r.update_hash,
                epsilon_spent=r.epsilon_spent,
            )
            for r in results
        ]

        agg_result = self.aggregator.aggregate(
            training_round.round_number,
            node_updates,
            min_updates=training_round.min_nodes_required,
        )

        if agg_result is None:
            training_round.status = TrainingRound.Status.FAILED
            training_round.save()
            return False

        # Phase 3 — Persist results
        training_round.global_accuracy = agg_result.global_accuracy
        training_round.global_loss = agg_result.global_loss
        training_round.status = TrainingRound.Status.COMPLETED
        training_round.completed_at = timezone.now()
        training_round.save()

        AggregationLog.objects.create(
            training_round=training_round,
            updates_received=agg_result.updates_accepted + agg_result.updates_rejected,
            updates_accepted=agg_result.updates_accepted,
            updates_rejected=agg_result.updates_rejected,
            total_samples=agg_result.total_samples,
            aggregation_time_seconds=agg_result.elapsed_seconds,
            global_model_path=agg_result.new_model_hash,
        )

        ThreatModel.objects.create(
            version=f"fl-r{training_round.round_number}",
            architecture='federated-ensemble',
            status=ThreatModel.Status.DEPLOYED,
            accuracy=agg_result.global_accuracy,
            training_round=training_round,
            deployed_at=timezone.now(),
        )

        logger.info("Round %d completed: global_acc=%s",
                     training_round.round_number, agg_result.global_accuracy)
        return True

    @staticmethod
    def _get_noise_multiplier(node: FederatedNode) -> float:
        budget = PrivacyBudget.objects.filter(node=node).first()
        return budget.noise_multiplier if budget else 1.1

    @staticmethod
    def _consume_budget(node: FederatedNode, epsilon_spent: float):
        budget, created = PrivacyBudget.objects.get_or_create(
            node=node,
            defaults={
                'epsilon': epsilon_spent,
                'max_epsilon': getattr(settings, 'FL_MAX_EPSILON', 10.0),
                'delta': getattr(settings, 'FL_DEFAULT_DELTA', 1e-5),
            },
        )
        if not created:
            budget.epsilon += epsilon_spent
            budget.rounds_consumed += 1
            budget.save()
