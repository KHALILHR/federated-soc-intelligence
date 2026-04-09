import uuid
from django.db import models
from django.conf import settings


class PlatformMetrics(models.Model):
    """Point-in-time snapshot of platform-wide telemetry."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    active_nodes = models.PositiveIntegerField(default=0)
    total_logs_ingested = models.BigIntegerField(default=0)
    threats_detected = models.PositiveIntegerField(default=0)
    global_model_accuracy = models.FloatField(default=0.0)
    avg_privacy_epsilon = models.FloatField(default=0.0)
    avg_inference_latency_ms = models.FloatField(default=0.0)
    active_training_rounds = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Platform metrics'
        get_latest_by = 'timestamp'

    def __str__(self):
        return f"Metrics @ {self.timestamp:%Y-%m-%d %H:%M}"


class AlertFeed(models.Model):
    """Security alerts surfaced on the dashboard."""

    class AlertLevel(models.TextChoices):
        INFO = 'info', 'Info'
        WARNING = 'warning', 'Warning'
        CRITICAL = 'critical', 'Critical'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    level = models.CharField(max_length=10, choices=AlertLevel.choices, default=AlertLevel.INFO)
    title = models.CharField(max_length=300)
    message = models.TextField()
    source_node = models.ForeignKey(
        'federated.FederatedNode',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alerts',
    )
    ioc = models.ForeignKey(
        'threat_detection.IOCEntry',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alerts',
    )
    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.level.upper()}] {self.title}"


class SystemHealth(models.Model):
    """Health check probes for platform components."""

    class Component(models.TextChoices):
        DJANGO = 'django', 'Django Application'
        ELASTICSEARCH = 'elasticsearch', 'Elasticsearch'
        AGGREGATOR = 'aggregator', 'FL Aggregator'
        DATABASE = 'database', 'Database'
        REDIS = 'redis', 'Redis / Message Broker'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    component = models.CharField(max_length=20, choices=Component.choices)
    is_healthy = models.BooleanField(default=True)
    latency_ms = models.FloatField(default=0.0)
    details = models.JSONField(default=dict, blank=True)
    checked_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-checked_at']
        verbose_name_plural = 'System health checks'

    def __str__(self):
        status = '✓' if self.is_healthy else '✗'
        return f"{status} {self.get_component_display()} @ {self.checked_at:%H:%M:%S}"
