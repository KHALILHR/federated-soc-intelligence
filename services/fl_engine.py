"""
Federated Learning Engine
Wraps PySyft / Flower client logic and provides a clean interface
for the Django views to trigger training without blocking the WSGI process.

In production this runs as a Celery task or a separate process;
the Django view only enqueues work and reads status from the DB.
"""

import logging
import time
import random
import hashlib
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class LocalTrainingResult:
    """Result payload returned by a single node's local training step."""
    node_id: str
    round_number: int
    accuracy: float = 0.0
    loss: float = 0.0
    num_samples: int = 0
    update_hash: str = ''
    epsilon_spent: float = 0.0
    elapsed_seconds: float = 0.0


class FederatedClient:
    """
    Simulates a Flower / PySyft federated-learning client.

    Replace the body of `train_local_round` with real framework calls:
        - Flower:  flwr.client.start_numpy_client(...)
        - PySyft:  sy.VirtualMachine / Domain ...
    """

    def __init__(self, node_id: str, aggregator_host: str = 'localhost',
                 aggregator_port: int = 8081):
        self.node_id = node_id
        self.aggregator_url = f"http://{aggregator_host}:{aggregator_port}"
        self._model_weights: Optional[bytes] = None

    def fetch_global_model(self) -> bytes:
        """Download the latest global model weights from the aggregator."""
        logger.info("Fetching global model from %s", self.aggregator_url)
        # --- Production: HTTP GET to aggregator /model/latest ---
        self._model_weights = hashlib.sha256(
            f"global-weights-{time.time()}".encode()
        ).digest()
        return self._model_weights

    def train_local_round(self, round_number: int,
                          epochs: int = 1,
                          learning_rate: float = 0.001,
                          noise_multiplier: float = 1.1,
                          clip_norm: float = 1.0) -> LocalTrainingResult:
        """
        Run one round of local training with differential-privacy noise.

        In production, swap the simulation block below with:
            model = load_model(self._model_weights)
            dp_optimizer = DPOptimizer(model.parameters(), noise_multiplier, clip_norm)
            for epoch in range(epochs):
                for batch in local_dataloader:
                    loss = criterion(model(batch.x), batch.y)
                    loss.backward()
                    dp_optimizer.step()
            return serialized_gradients
        """
        start = time.time()
        logger.info(
            "Node %s — local training round %d (lr=%s, σ=%s)",
            self.node_id, round_number, learning_rate, noise_multiplier,
        )

        # Simulated training metrics
        simulated_accuracy = round(random.uniform(0.82, 0.97), 4)
        simulated_loss = round(random.uniform(0.03, 0.35), 4)
        simulated_samples = random.randint(500, 5000)
        epsilon_cost = round(noise_multiplier * epochs * 0.05, 6)

        gradient_blob = hashlib.sha256(
            f"{self.node_id}-round-{round_number}-{time.time()}".encode()
        ).hexdigest()

        elapsed = round(time.time() - start, 3)

        result = LocalTrainingResult(
            node_id=self.node_id,
            round_number=round_number,
            accuracy=simulated_accuracy,
            loss=simulated_loss,
            num_samples=simulated_samples,
            update_hash=gradient_blob,
            epsilon_spent=epsilon_cost,
            elapsed_seconds=elapsed,
        )
        logger.info("Node %s — round %d complete: acc=%s loss=%s ε=%s",
                     self.node_id, round_number,
                     result.accuracy, result.loss, result.epsilon_spent)
        return result

    def submit_update(self, result: LocalTrainingResult) -> bool:
        """Push gradient update to the aggregator."""
        logger.info("Submitting update for round %d to %s",
                     result.round_number, self.aggregator_url)
        # --- Production: HTTP POST to aggregator /update ---
        return True
