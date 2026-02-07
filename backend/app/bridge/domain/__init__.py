"""
Domain models e schemas do PPBridge Service.
"""
from .enums import FlowStatus, EventType, AdapterDomain, AdapterType, can_transition
from .schemas import (
    SourceTargetSchema,
    BridgeFlowCreateRequest,
    FlowEventResponse,
    BridgeFlowResponse,
    ErrorResponse,
    WebhookPayload,
)

__all__ = [
    'FlowStatus',
    'EventType',
    'AdapterDomain',
    'AdapterType',
    'can_transition',
    'SourceTargetSchema',
    'BridgeFlowCreateRequest',
    'FlowEventResponse',
    'BridgeFlowResponse',
    'ErrorResponse',
    'WebhookPayload',
]
