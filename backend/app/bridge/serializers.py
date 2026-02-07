"""
Serializers DRF para PPBridge API.
"""
from rest_framework import serializers
from .models import BridgeFlow, FlowEvent


class SourceTargetSerializer(serializers.Serializer):
    """Serializer para source/target."""
    domain = serializers.CharField()
    adapter = serializers.CharField()


class BridgeFlowCreateSerializer(serializers.Serializer):
    """Serializer para criar flow."""
    source = SourceTargetSerializer()
    target = SourceTargetSerializer()
    asset = serializers.CharField()
    amount = serializers.DecimalField(max_digits=20, decimal_places=8, min_value=0)
    callback_url = serializers.URLField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False, default=dict)
    source_metadata = serializers.JSONField(required=False, default=dict)
    target_metadata = serializers.JSONField(required=False, default=dict)


class FlowEventSerializer(serializers.ModelSerializer):
    """Serializer para eventos."""
    
    class Meta:
        model = FlowEvent
        fields = [
            'event_id',
            'event_type',
            'from_state',
            'to_state',
            'timestamp',
            'metadata',
        ]


class BridgeFlowSerializer(serializers.ModelSerializer):
    """Serializer para flow."""
    source = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()
    links = serializers.SerializerMethodField()
    
    class Meta:
        model = BridgeFlow
        fields = [
            'flow_id',
            'status',
            'source',
            'target',
            'asset',
            'amount',
            'result',
            'error_code',
            'error_message',
            'created_at',
            'updated_at',
            'completed_at',
            'links',
        ]
    
    def get_source(self, obj):
        return {
            'domain': obj.source_domain,
            'adapter': obj.source_adapter,
            'metadata': obj.source_metadata,
        }
    
    def get_target(self, obj):
        return {
            'domain': obj.target_domain,
            'adapter': obj.target_adapter,
            'metadata': obj.target_metadata,
        }
    
    def get_links(self, obj):
        request = self.context.get('request')
        if request:
            base_url = request.build_absolute_uri('/api/v1/bridge/flows/')
            return {
                'self': f"{base_url}{obj.flow_id}/",
                'events': f"{base_url}{obj.flow_id}/events/",
            }
        return {}
