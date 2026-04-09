from django.contrib import admin
from .models import ThreatModel, IOCEntry, DetectionRule, ThreatScore


@admin.register(ThreatModel)
class ThreatModelAdmin(admin.ModelAdmin):
    list_display = ('version', 'architecture', 'status', 'accuracy', 'f1_score', 'created_at')
    list_filter = ('status', 'architecture')


@admin.register(IOCEntry)
class IOCEntryAdmin(admin.ModelAdmin):
    list_display = ('ioc_type', 'value', 'enrichment_score', 'confidence', 'severity', 'is_active')
    list_filter = ('ioc_type', 'severity', 'is_active')
    search_fields = ('value',)


@admin.register(DetectionRule)
class DetectionRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'severity', 'enabled', 'hits', 'last_triggered')
    list_filter = ('rule_type', 'severity', 'enabled')
    search_fields = ('name',)


@admin.register(ThreatScore)
class ThreatScoreAdmin(admin.ModelAdmin):
    list_display = ('log_entry', 'model', 'score', 'label', 'inference_time_ms')
    list_filter = ('label',)
