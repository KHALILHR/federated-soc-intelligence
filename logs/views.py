import json
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone

from logs.models import LogSource, IngestionBatch, SIEMLogEntry
from services.log_ingestion import generate_log_entries


def local_node_view(request):
    """Local Node View — real-time log ingestion visualization."""
    sources = LogSource.objects.all()
    batches = IngestionBatch.objects.all()[:20]
    recent_logs = SIEMLogEntry.objects.all()[:50]

    # If no data, show demo state
    if not recent_logs.exists():
        demo_entries = generate_log_entries(count=30, source_name='demo-firewall')
    else:
        demo_entries = None

    severity_counts = {
        'critical': SIEMLogEntry.objects.filter(severity='critical').count(),
        'high': SIEMLogEntry.objects.filter(severity='high').count(),
        'medium': SIEMLogEntry.objects.filter(severity='medium').count(),
        'low': SIEMLogEntry.objects.filter(severity='low').count(),
    }

    # Fallback demo severity counts
    if sum(severity_counts.values()) == 0:
        severity_counts = {'critical': 23, 'high': 87, 'medium': 156, 'low': 412}

    context = {
        'sources': sources,
        'batches': batches,
        'recent_logs': recent_logs,
        'demo_entries': demo_entries,
        'severity_counts': severity_counts,
        'severity_json': json.dumps(severity_counts),
    }
    return render(request, 'logs/local_node.html', context)


def api_simulate_ingestion(request):
    """API endpoint that simulates ingesting a batch of logs."""
    count = int(request.GET.get('count', 25))
    entries = generate_log_entries(count=count)

    saved = 0
    batch = None
    first_source = LogSource.objects.first()

    if first_source:
        batch = IngestionBatch.objects.create(
            source=first_source,
            status='completed',
            record_count=len(entries),
            byte_size=sum(len(str(e)) for e in entries),
            elasticsearch_index=f"siem-logs-{timezone.now():%Y.%m}",
            started_at=timezone.now(),
            completed_at=timezone.now(),
        )
        for entry_data in entries:
            SIEMLogEntry.objects.create(
                batch=batch,
                timestamp=entry_data['timestamp'],
                source_ip=entry_data['source_ip'],
                destination_ip=entry_data['destination_ip'],
                event_type=entry_data['event_type'],
                severity=entry_data['severity'],
                raw_hash=entry_data['raw_hash'],
                parsed_fields=entry_data['parsed_fields'],
            )
            saved += 1

    return JsonResponse({
        'status': 'ok',
        'generated': len(entries),
        'saved': saved,
        'batch_id': str(batch.id) if batch else None,
        'sample': entries[:3],
    })


def api_log_stream(request):
    """Returns recent log entries as JSON for live-updating UI."""
    limit = int(request.GET.get('limit', 20))
    logs = SIEMLogEntry.objects.all()[:limit]

    if logs.exists():
        data = [
            {
                'id': str(l.id),
                'timestamp': l.timestamp.isoformat(),
                'source_ip': l.source_ip,
                'destination_ip': l.destination_ip,
                'event_type': l.event_type,
                'severity': l.severity,
                'threat_score': l.threat_score,
            }
            for l in logs
        ]
    else:
        entries = generate_log_entries(count=limit)
        data = [
            {
                'id': e['id'],
                'timestamp': e['timestamp'].isoformat(),
                'source_ip': e['source_ip'],
                'destination_ip': e['destination_ip'],
                'event_type': e['event_type'],
                'severity': e['severity'],
                'threat_score': None,
            }
            for e in entries
        ]

    return JsonResponse({'logs': data})
