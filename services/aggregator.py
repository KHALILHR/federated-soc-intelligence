"""
Aggregation Service
Implements FedAvg and variant strategies for combining gradient updates
received from participating nodes.

This module is called by the Round Manager after all nodes submit updates.
In a Docker deployment, this runs on the aggregator container;
the Django app communicates with it via HTTP.
"""

import logging
import time
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class NodeUpdate:
    """Represents one node's submitted gradient update."""
    node_id: str
    num_samples: int
    accuracy: float
    loss: float
    update_hash: str
    epsilon_spent: float


@dataclass
class AggregationResult:
    """Result of aggregating all submitted updates into a new global model."""
    round_number: int
    global_accuracy: float
    global_loss: float
    updates_accepted: int
    updates_rejected: int
    total_samples: int
    elapsed_seconds: float
    new_model_hash: str


class Aggregator:
    """
    FedAvg aggregation engine.

    Strategies:
        - fedavg:   Weighted averaging by sample count.
        - fedprox:  FedAvg + proximal term penalty (μ parameter).
        - scaffold: Variance-reduction corrected updates.
    """

    SUPPORTED_STRATEGIES = ('fedavg', 'fedprox', 'scaffold')

    def __init__(self, strategy: str = 'fedavg', mu: float = 0.01):
        if strategy not in self.SUPPORTED_STRATEGIES:
            raise ValueError(f"Unknown strategy '{strategy}'. Choose from {self.SUPPORTED_STRATEGIES}")
        self.strategy = strategy
        self.mu = mu

    def aggregate(self, round_number: int,
                  updates: List[NodeUpdate],
                  min_updates: int = 2) -> Optional[AggregationResult]:
        """
        Aggregate gradient updates using the configured strategy.

        In production, replace the simulation with actual tensor averaging:
            global_weights = sum(
                (u.num_samples / total_samples) * deserialize(u.update)
                for u in accepted_updates
            )
        """
        start = time.time()

        if len(updates) < min_updates:
            logger.warning(
                "Round %d: only %d updates received (need %d). Skipping.",
                round_number, len(updates), min_updates,
            )
            return None

        accepted = [u for u in updates if self._validate_update(u)]
        rejected = len(updates) - len(accepted)

        if not accepted:
            logger.warning("Round %d: all updates rejected.", round_number)
            return None

        total_samples = sum(u.num_samples for u in accepted)

        # Weighted average metrics (simulated)
        global_accuracy = sum(
            u.accuracy * (u.num_samples / total_samples) for u in accepted
        )
        global_loss = sum(
            u.loss * (u.num_samples / total_samples) for u in accepted
        )

        if self.strategy == 'fedprox':
            global_loss += self.mu * 0.01  # Proximal regularization term

        elapsed = round(time.time() - start, 3)

        result = AggregationResult(
            round_number=round_number,
            global_accuracy=round(global_accuracy, 4),
            global_loss=round(global_loss, 4),
            updates_accepted=len(accepted),
            updates_rejected=rejected,
            total_samples=total_samples,
            elapsed_seconds=elapsed,
            new_model_hash=f"global-model-round-{round_number}",
        )
        logger.info(
            "Round %d aggregated: acc=%s loss=%s (%d/%d updates accepted)",
            round_number, result.global_accuracy, result.global_loss,
            result.updates_accepted, len(updates),
        )
        return result

    @staticmethod
    def _validate_update(update: NodeUpdate) -> bool:
        """Basic sanity check on a submitted update."""
        if update.num_samples <= 0:
            return False
        if not (0.0 <= update.accuracy <= 1.0):
            return False
        return True
