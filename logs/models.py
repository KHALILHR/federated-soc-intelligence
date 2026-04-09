import uuid
from django.db import models
from django.conf import settings


class LogSource(models.Model):
    """A registered SIEM log source (firewall, IDS, endpoint, etc.)."""

    class SourceType(models.TextChoices):
        FIREWALL = 'firewall', 'Firewall'
        IDS = 'ids', 'Intrusion Detection System'
        ENDPOINT = 'endpoint', 'Endpoint Agent'
        CLOUD = 'cloud', 'Cloud Service'
        AUTH = 'auth', 'Authentication Service'
        DNS = 'dns', 'DNS Server'
        PROXY = 'proxy', 'Web Proxy'
        CUSTOM = 'custom', 'Custom Source'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    host = models.GenericIPAddressField(help_text='IP address of the log source')
    port = models.PositiveIntegerField(default=514)
    protocol = models.CharField(
        max_length=10,
        choices=[('tcp', 'TCP'), ('udp', 'UDP'), ('tls', 'TLS')],
        default='tcp',
    )
    is_active = models.BooleanField(default=True)
    node = models.ForeignKey(
        'federated.FederatedNode',
        on_delete=models.CASCADE,
        related_name='log_sources',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['host', 'port', 'node']

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()}) @ {self.host}"


class IngestionBatch(models.Model):
    """Tracks a batch of logs ingested from a source into Elasticsearch."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        INGESTING = 'ingesting', 'Ingesting'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(LogSource, on_delete=models.CASCADE, related_name='batches')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    record_count = models.PositiveIntegerField(default=0)
    byte_size = models.BigIntegerField(default=0, help_text='Total payload size in bytes')
    elasticsearch_index = models.CharField(
        max_length=255,
        blank=True,
        help_text='Target ES index name (e.g., siem-logs-2026.04)',
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Ingestion batches'

    def __str__(self):
        return f"Batch {self.id.hex[:8]} — {self.source.name} ({self.status})"

    @property
    def throughput_mbps(self):
        if self.started_at and self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            if duration > 0:
                return round((self.byte_size / 1_048_576) / duration, 2)
        return 0.0


class SIEMLogEntry(models.Model):
    """Metadata record for an individual log event (raw payload stored in ES)."""

    class Severity(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name='entries')
    timestamp = models.DateTimeField(help_text='Original event timestamp from source')
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    destination_ip = models.GenericIPAddressField(null=True, blank=True)
    event_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.LOW)
    raw_hash = models.CharField(max_length=64, help_text='SHA-256 hash of the raw log line')
    parsed_fields = models.JSONField(default=dict, blank=True)
    threat_score = models.FloatField(
        null=True, blank=True,
        help_text='Score assigned by the threat detection model (0.0 – 1.0)',
    )
    indexed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'SIEM log entry'
        verbose_name_plural = 'SIEM log entries'

    def __str__(self):
        return f"[{self.severity.upper()}] {self.event_type} @ {self.timestamp}"
