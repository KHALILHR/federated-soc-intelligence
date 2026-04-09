from django.contrib import admin
from .models import PlatformMetrics, AlertFeed, SystemHealth


@admin.register(PlatformMetrics)
class PlatformMetricsAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp', 'active_nodes', 'total_logs_ingested',
        'threats_detected', 'global_model_accuracy',
    )


@admin.register(AlertFeed)
class AlertFeedAdmin(admin.ModelAdmin):
    list_display = ('level', 'title', 'source_node', 'acknowledged', 'created_at')
    list_filter = ('level', 'acknowledged')
    search_fields = ('title', 'message')


@admin.register(SystemHealth)
class SystemHealthAdmin(admin.ModelAdmin):
    list_display = ('component', 'is_healthy', 'latency_ms', 'checked_at')
    list_filter = ('component', 'is_healthy')
