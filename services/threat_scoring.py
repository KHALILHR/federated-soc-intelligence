"""
Threat Scoring Service
Runs inference using the latest deployed ThreatModel against incoming log entries.
Designed to be called asynchronously (Celery / subprocess) so the Django
web server is never blocked by heavy ML inference.
"""

import logging
import random
import time
from dataclasses import dataclass
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

ATTACK_LABELS = [
    'benign', 'malware', 'phishing', 'c2_beacon', 'data_exfiltration',
    'brute_force', 'lateral_movement', 'privilege_escalation',
    'dos', 'reconnaissance',
]


@dataclass
class InferenceResult:
    """Single inference result for one log entry."""
    log_entry_id: str
    score: float
    label: str
    confidence: float
    inference_time_ms: float


class ThreatScoringEngine:
    """
    Loads the latest global model and scores log entries.

    In production, swap the simulation with:
        model = torch.load(model_path)
        model.eval()
        with torch.no_grad():
            output = model(feature_tensor)
            score = torch.sigmoid(output).item()
    """

    def __init__(self, model_path: str = '', model_version: str = 'latest'):
        self.model_path = model_path
        self.model_version = model_version
        self._model = None

    def load_model(self):
        """Load model weights from disk or model registry."""
        logger.info("Loading threat model v%s from %s",
                     self.model_version, self.model_path or '<in-memory>')
        # Production: self._model = torch.load(self.model_path)
        self._model = True  # Placeholder for loaded model reference
        return self._model is not None

    def score_entry(self, features: Dict[str, Any]) -> InferenceResult:
        """Score a single log entry."""
        start = time.time()

        # Simulated inference
        is_threat = random.random() < 0.15  # ~15% threat rate simulation
        if is_threat:
            score = round(random.uniform(0.65, 0.99), 4)
            label = random.choice(ATTACK_LABELS[1:])  # Exclude 'benign'
        else:
            score = round(random.uniform(0.01, 0.30), 4)
            label = 'benign'

        confidence = round(random.uniform(0.70, 0.99), 4)
        elapsed_ms = round((time.time() - start) * 1000, 2)

        return InferenceResult(
            log_entry_id=features.get('id', ''),
            score=score,
            label=label,
            confidence=confidence,
            inference_time_ms=elapsed_ms,
        )

    def score_batch(self, entries: List[Dict[str, Any]]) -> List[InferenceResult]:
        """Score a batch of log entries."""
        results = []
        for entry in entries:
            results.append(self.score_entry(entry))
        logger.info("Scored %d entries (model v%s)", len(results), self.model_version)
        return results
