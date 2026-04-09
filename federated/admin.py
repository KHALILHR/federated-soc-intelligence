from django.contrib import admin
from .models import (
    FederatedNode, PrivacyBudget, TrainingRound,
    GradientUpdate, AggregationLog,
)


@admin.register(FederatedNode)
class FederatedNodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'host', 'port', 'organization', 'status', 'last_heartbeat')
    list_filter = ('status', 'organization')
    search_fields = ('name', 'host')


@admin.register(PrivacyBudget)
class PrivacyBudgetAdmin(admin.ModelAdmin):
    list_display = ('node', 'epsilon', 'delta', 'max_epsilon', 'budget_remaining_pct', 'rounds_consumed')
    list_filter = ('node',)
    readonly_fields = ('budget_remaining_pct', 'is_exhausted')


@admin.register(TrainingRound)
class TrainingRoundAdmin(admin.ModelAdmin):
    list_display = ('round_number', 'status', 'global_accuracy', 'aggregation_strategy', 'started_at')
    list_filter = ('status', 'aggregation_strategy')


@admin.register(GradientUpdate)
class GradientUpdateAdmin(admin.ModelAdmin):
    list_display = ('node', 'training_round', 'local_accuracy', 'epsilon_spent', 'accepted', 'submitted_at')
    list_filter = ('accepted', 'training_round')


@admin.register(AggregationLog)
class AggregationLogAdmin(admin.ModelAdmin):
    list_display = ('training_round', 'updates_received', 'updates_accepted', 'aggregation_time_seconds')
