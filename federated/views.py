import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from federated.models import (
    FederatedNode, TrainingRound, GradientUpdate,
    PrivacyBudget, AggregationLog,
)


def federation_overview(request):
    """Overview of the federated network: nodes, rounds, privacy budgets."""
    nodes = FederatedNode.objects.all()
    rounds = TrainingRound.objects.all()[:20]
    budgets = PrivacyBudget.objects.select_related('node').all()

    # Privacy budget chart data
    budget_labels = []
    budget_used = []
    budget_remaining = []
    for b in budgets:
        budget_labels.append(b.node.name)
        budget_used.append(round(float(b.epsilon), 4))
        budget_remaining.append(round(float(b.max_epsilon - b.epsilon), 4))

    # Demo data fallback
    if not budget_labels:
        budget_labels = ['SOC-Paris', 'SOC-London', 'SOC-NewYork', 'SOC-Tokyo', 'SOC-Sydney']
        budget_used = [2.3, 1.8, 3.5, 1.2, 0.9]
        budget_remaining = [7.7, 8.2, 6.5, 8.8, 9.1]

    # Round history
    round_history = []
    for r in rounds:
        updates = GradientUpdate.objects.filter(training_round=r)
        round_history.append({
            'number': r.round_number,
            'status': r.status,
            'accuracy': r.global_accuracy,
            'loss': r.global_loss,
            'strategy': r.aggregation_strategy,
            'nodes': r.participating_nodes.count(),
            'updates': updates.count(),
            'started': r.started_at,
            'completed': r.completed_at,
        })

    if not round_history:
        round_history = [
            {'number': i, 'status': 'completed', 'accuracy': round(0.78 + i*0.01, 4),
             'loss': round(0.35 - i*0.015, 4), 'strategy': 'fedavg', 'nodes': 5,
             'updates': 5, 'started': None, 'completed': None}
            for i in range(1, 11)
        ]

    context = {
        'nodes': nodes,
        'rounds': rounds,
        'budgets': budgets,
        'budget_labels': json.dumps(budget_labels),
        'budget_used': json.dumps(budget_used),
        'budget_remaining': json.dumps(budget_remaining),
        'round_history': round_history,
    }
    return render(request, 'federated/overview.html', context)


@csrf_exempt
@require_POST
def api_trigger_round(request):
    """API endpoint to trigger a new federated training round."""
    from services.round_manager import RoundManager

    strategy = request.POST.get('strategy', 'fedavg')
    manager = RoundManager(strategy=strategy)

    try:
        training_round = manager.create_round()
        success = manager.execute_round(training_round)
        return JsonResponse({
            'status': 'completed' if success else 'failed',
            'round_number': training_round.round_number,
            'global_accuracy': training_round.global_accuracy,
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def api_node_status(request):
    """API endpoint for node status information."""
    nodes = FederatedNode.objects.all()
    if nodes.exists():
        data = [
            {
                'id': str(n.id),
                'name': n.name,
                'status': n.status,
                'host': n.host,
                'last_heartbeat': n.last_heartbeat.isoformat() if n.last_heartbeat else None,
                'total_samples': n.total_samples,
            }
            for n in nodes
        ]
    else:
        data = [
            {'id': f'demo-{i}', 'name': name, 'status': status,
             'host': f'10.0.{i}.1', 'last_heartbeat': None, 'total_samples': samples}
            for i, (name, status, samples) in enumerate([
                ('SOC-Paris', 'online', 12400), ('SOC-London', 'online', 9800),
                ('SOC-NewYork', 'training', 15200), ('SOC-Tokyo', 'online', 8900),
                ('SOC-Sydney', 'offline', 6700),
            ], 1)
        ]
    return JsonResponse({'nodes': data})
