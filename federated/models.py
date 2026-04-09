import uuid
from django.db import models
from django.conf import settings


class FederatedNode(models.Model):
    """A participating node in the federated learning network."""

    class Status(models.TextChoices):
        ONLINE = 'online', 'Online'
        OFFLINE = 'offline', 'Offline'
        TRAINING = 'training', 'Training'
        SYNCING = 'syncing', 'Syncing'
        ERROR = 'error', 'Error'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    host = models.GenericIPAddressField(help_text='Node container IP or hostname')
    port = models.PositiveIntegerField(default=8081)
    organization = models.ForeignKey(
        'users.Organization',
        on_delete=models.CASCADE,
        related_name='nodes',
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OFFLINE)
    cpu_cores = models.PositiveSmallIntegerField(default=4)
    memory_gb = models.FloatField(default=8.0)
    gpu_available = models.BooleanField(default=False)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    total_samples = models.PositiveIntegerField(
        default=0, help_text='Number of local training samples',
    )
    latitude = models.FloatField(null=True, blank=True, help_text='Geographic latitude')
    longitude = models.FloatField(null=True, blank=True, help_text='Geographic longitude')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.status})"


class PrivacyBudget(models.Model):
    """Tracks differential privacy budget consumption per node per round."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node = models.ForeignKey(FederatedNode, on_delete=models.CASCADE, related_name='privacy_budgets')
    epsilon = models.FloatField(
        default=1.0,
        help_text='Current cumulative epsilon (privacy loss parameter)',
    )
    delta = models.FloatField(
        default=1e-5,
        help_text='Delta parameter for (ε, δ)-differential privacy',
    )
    max_epsilon = models.FloatField(
        default=10.0,
        help_text='Maximum allowed cumulative epsilon before halting',
    )
    noise_multiplier = models.FloatField(
        default=1.1,
        help_text='Gaussian noise multiplier applied to gradients',
    )
    clip_norm = models.FloatField(
        default=1.0,
        help_text='Gradient clipping L2 norm bound',
    )
    rounds_consumed = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Budget [{self.node.name}] ε={self.epsilon:.4f} δ={self.delta}"

    @property
    def budget_remaining_pct(self):
        if self.max_epsilon > 0:
            return max(0.0, round((1 - self.epsilon / self.max_epsilon) * 100, 2))
        return 0.0

    @property
    def is_exhausted(self):
        return self.epsilon >= self.max_epsilon


class TrainingRound(models.Model):
    """A single federated training round coordinated by the aggregator."""

    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        IN_PROGRESS = 'in_progress', 'In Progress'
        AGGREGATING = 'aggregating', 'Aggregating'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    round_number = models.PositiveIntegerField(unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    participating_nodes = models.ManyToManyField(
        FederatedNode, blank=True, related_name='training_rounds',
    )
    global_accuracy = models.FloatField(null=True, blank=True)
    global_loss = models.FloatField(null=True, blank=True)
    aggregation_strategy = models.CharField(
        max_length=30, default='fedavg',
        help_text='Aggregation algorithm (fedavg, fedprox, scaffold)',
    )
    min_nodes_required = models.PositiveSmallIntegerField(default=2)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-round_number']

    def __str__(self):
        return f"Round {self.round_number} ({self.status})"


class GradientUpdate(models.Model):
    """A gradient/weight update submitted by a node for a training round."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    training_round = models.ForeignKey(
        TrainingRound, on_delete=models.CASCADE, related_name='gradient_updates',
    )
    node = models.ForeignKey(FederatedNode, on_delete=models.CASCADE, related_name='gradient_updates')
    local_accuracy = models.FloatField(default=0.0)
    local_loss = models.FloatField(default=0.0)
    num_samples = models.PositiveIntegerField(default=0)
    update_size_bytes = models.BigIntegerField(default=0)
    update_path = models.CharField(
        max_length=500, blank=True,
        help_text='Path or URI to the serialized gradient tensor',
    )
    epsilon_spent = models.FloatField(
        default=0.0,
        help_text='Privacy budget consumed in this update',
    )
    accepted = models.BooleanField(
        default=False,
        help_text='Whether the aggregator accepted this update',
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['training_round', 'node']

    def __str__(self):
        return f"Update from {self.node.name} for Round {self.training_round.round_number}"


class AggregationLog(models.Model):
    """Audit log for the aggregation step of each training round."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    training_round = models.OneToOneField(
        TrainingRound, on_delete=models.CASCADE, related_name='aggregation_log',
    )
    updates_received = models.PositiveIntegerField(default=0)
    updates_accepted = models.PositiveIntegerField(default=0)
    updates_rejected = models.PositiveIntegerField(default=0)
    total_samples = models.PositiveIntegerField(default=0)
    aggregation_time_seconds = models.FloatField(default=0.0)
    global_model_path = models.CharField(max_length=500, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Aggregation for Round {self.training_round.round_number}"
