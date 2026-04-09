import json
import random
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

from federated.models import FederatedNode, TrainingRound, PrivacyBudget
from threat_detection.models import ThreatModel, IOCEntry
from logs.models import IngestionBatch, SIEMLogEntry
from dashboard.models import PlatformMetrics, AlertFeed, SystemHealth


def _generate_demo_metrics():
    """Generate demonstration metrics when the database is empty."""
    return {
        'active_nodes': 5,
        'total_logs': 148320,
        'threats_detected': 1247,
        'global_accuracy': 0.9432,
        'avg_epsilon': 2.34,
        'avg_latency': 12.8,
        'active_rounds': 1,
    }


def index(request):
    """Global Dashboard — primary landing page with all telemetry."""
    nodes = FederatedNode.objects.all()
    rounds = TrainingRound.objects.all()[:20]
    latest_model = ThreatModel.objects.filter(status='deployed').first()
    recent_alerts = AlertFeed.objects.all()[:10]
    health_checks = SystemHealth.objects.all()

    # Metrics — use real data if available, else demo data
    metrics_obj = PlatformMetrics.objects.first()
    if metrics_obj:
        metrics = {
            'active_nodes': metrics_obj.active_nodes,
            'total_logs': metrics_obj.total_logs_ingested,
            'threats_detected': metrics_obj.threats_detected,
            'global_accuracy': metrics_obj.global_model_accuracy,
            'avg_epsilon': metrics_obj.avg_privacy_epsilon,
            'avg_latency': metrics_obj.avg_inference_latency_ms,
            'active_rounds': metrics_obj.active_training_rounds,
        }
    else:
        metrics = _generate_demo_metrics()

    # Accuracy vs Privacy Budget chart data
    accuracy_data = []
    privacy_data = []
    round_labels = []
    for r in reversed(list(rounds)):
        round_labels.append(f"R{r.round_number}")
        accuracy_data.append(float(r.global_accuracy or 0))
        budgets = PrivacyBudget.objects.filter(
            node__training_rounds=r
        ).values_list('epsilon', flat=True)
        avg_eps = sum(budgets) / len(budgets) if budgets else 0
        privacy_data.append(round(float(avg_eps), 4))

    # If no real data, generate demo chart data
    if not round_labels:
        round_labels = [f"R{i}" for i in range(1, 16)]
        accuracy_data = [round(0.75 + i * 0.012 + random.uniform(-0.005, 0.005), 4) for i in range(15)]
        privacy_data = [round(0.5 + i * 0.45 + random.uniform(-0.05, 0.05), 4) for i in range(15)]

    # Node map data
    node_map_data = []
    if nodes.exists():
        for n in nodes:
            node_map_data.append({
                'name': n.name,
                'lat': float(n.latitude or 0),
                'lng': float(n.longitude or 0),
                'status': n.status,
                'samples': n.total_samples,
            })
    else:
        node_map_data = [
            {'name': 'SOC-Paris', 'lat': 48.8566, 'lng': 2.3522, 'status': 'online', 'samples': 12400},
            {'name': 'SOC-London', 'lat': 51.5074, 'lng': -0.1278, 'status': 'online', 'samples': 9800},
            {'name': 'SOC-NewYork', 'lat': 40.7128, 'lng': -74.0060, 'status': 'training', 'samples': 15200},
            {'name': 'SOC-Tokyo', 'lat': 35.6762, 'lng': 139.6503, 'status': 'online', 'samples': 8900},
            {'name': 'SOC-Sydney', 'lat': -33.8688, 'lng': 151.2093, 'status': 'offline', 'samples': 6700},
        ]

    context = {
        'metrics': metrics,
        'nodes': nodes,
        'rounds': rounds,
        'latest_model': latest_model,
        'recent_alerts': recent_alerts,
        'health_checks': health_checks,
        'chart_labels': json.dumps(round_labels),
        'accuracy_data': json.dumps(accuracy_data),
        'privacy_data': json.dumps(privacy_data),
        'node_map_data': json.dumps(node_map_data),
    }
    return render(request, 'dashboard/index.html', context)


def api_metrics(request):
    """REST endpoint returning current platform metrics as JSON."""
    metrics_obj = PlatformMetrics.objects.first()
    if metrics_obj:
        data = {
            'active_nodes': metrics_obj.active_nodes,
            'total_logs_ingested': metrics_obj.total_logs_ingested,
            'threats_detected': metrics_obj.threats_detected,
            'global_model_accuracy': metrics_obj.global_model_accuracy,
            'avg_privacy_epsilon': metrics_obj.avg_privacy_epsilon,
            'timestamp': metrics_obj.timestamp.isoformat(),
        }
    else:
        data = _generate_demo_metrics()
        data['timestamp'] = timezone.now().isoformat()
    return JsonResponse(data)


def api_alerts(request):
    """REST endpoint returning recent alerts as JSON."""
    alerts = AlertFeed.objects.all()[:20]
    data = [
        {
            'id': str(a.id),
            'level': a.level,
            'title': a.title,
            'message': a.message,
            'acknowledged': a.acknowledged,
            'created_at': a.created_at.isoformat(),
        }
        for a in alerts
    ]
    return JsonResponse({'alerts': data})
