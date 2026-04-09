import uuid
from django.db import models
from django.conf import settings


class ThreatModel(models.Model):
    """Registry of trained ML model versions used for threat scoring."""

    class Status(models.TextChoices):
        TRAINING = 'training', 'Training'
        VALIDATING = 'validating', 'Validating'
        DEPLOYED = 'deployed', 'Deployed'
        RETIRED = 'retired', 'Retired'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.CharField(max_length=20, unique=True)
    architecture = models.CharField(
        max_length=50,
        help_text='Model architecture identifier (e.g., transformer-v2, lstm-attention)',
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRAINING)
    accuracy = models.FloatField(default=0.0, help_text='Validation accuracy (0.0 – 1.0)')
    f1_score = models.FloatField(default=0.0)
    false_positive_rate = models.FloatField(default=0.0)
    training_round = models.ForeignKey(
        'federated.TrainingRound',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='produced_models',
    )
    parameters_path = models.CharField(
        max_length=500, blank=True,
        help_text='Path or URI to serialized model weights',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    deployed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"ThreatModel v{self.version} ({self.status})"


class IOCEntry(models.Model):
    """Indicator of Compromise enriched with model-generated scores."""

    class IOCType(models.TextChoices):
        IP = 'ip', 'IP Address'
        DOMAIN = 'domain', 'Domain'
        URL = 'url', 'URL'
        HASH_MD5 = 'md5', 'MD5 Hash'
        HASH_SHA256 = 'sha256', 'SHA-256 Hash'
        EMAIL = 'email', 'Email Address'
        CVE = 'cve', 'CVE Identifier'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ioc_type = models.CharField(max_length=10, choices=IOCType.choices)
    value = models.CharField(max_length=500, db_index=True)
    enrichment_score = models.FloatField(
        default=0.0,
        help_text='Threat enrichment score from the global model (0.0 – 1.0)',
    )
    confidence = models.FloatField(default=0.0, help_text='Confidence level (0.0 – 1.0)')
    severity = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'), ('medium', 'Medium'),
            ('high', 'High'), ('critical', 'Critical'),
        ],
        default='low',
    )
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    source_feeds = models.JSONField(
        default=list, blank=True,
        help_text='List of intel feed names that reported this IOC',
    )
    associated_model = models.ForeignKey(
        ThreatModel, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='iocs',
    )
    tags = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-enrichment_score']
        verbose_name = 'IOC entry'
        verbose_name_plural = 'IOC entries'
        unique_together = ['ioc_type', 'value']

    def __str__(self):
        return f"[{self.ioc_type.upper()}] {self.value} (score: {self.enrichment_score})"


class DetectionRule(models.Model):
    """A detection rule (YARA/Sigma-style) applied on ingested logs."""

    class RuleType(models.TextChoices):
        SIGMA = 'sigma', 'Sigma Rule'
        YARA = 'yara', 'YARA Rule'
        CUSTOM = 'custom', 'Custom ML Rule'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    rule_type = models.CharField(max_length=10, choices=RuleType.choices)
    description = models.TextField(blank=True)
    logic = models.TextField(help_text='Rule definition body (Sigma YAML, YARA syntax, or JSON)')
    severity = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'), ('medium', 'Medium'),
            ('high', 'High'), ('critical', 'Critical'),
        ],
        default='medium',
    )
    enabled = models.BooleanField(default=True)
    hits = models.PositiveIntegerField(default=0)
    last_triggered = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-hits']

    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"


class ThreatScore(models.Model):
    """Individual threat score produced by running a model against a log entry."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    log_entry = models.ForeignKey(
        'logs.SIEMLogEntry',
        on_delete=models.CASCADE,
        related_name='scores',
    )
    model = models.ForeignKey(ThreatModel, on_delete=models.CASCADE, related_name='scores')
    score = models.FloatField(help_text='Threat probability (0.0 – 1.0)')
    label = models.CharField(
        max_length=50, blank=True,
        help_text='Predicted class label (e.g., malware, phishing, benign)',
    )
    inference_time_ms = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score']
        unique_together = ['log_entry', 'model']

    def __str__(self):
        return f"Score {self.score:.3f} — {self.label}"
