from django.contrib import admin
from .models import LogSource, IngestionBatch, SIEMLogEntry


@admin.register(LogSource)
class LogSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_type', 'host', 'port', 'is_active', 'node')
    list_filter = ('source_type', 'is_active')
    search_fields = ('name', 'host')


@admin.register(IngestionBatch)
class IngestionBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'source', 'status', 'record_count', 'byte_size', 'created_at')
    list_filter = ('status',)
    readonly_fields = ('throughput_mbps',)


@admin.register(SIEMLogEntry)
class SIEMLogEntryAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'severity', 'source_ip', 'destination_ip', 'timestamp', 'threat_score')
    list_filter = ('severity', 'event_type')
    search_fields = ('source_ip', 'destination_ip', 'event_type')
