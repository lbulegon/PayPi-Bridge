"""
Schemas Pydantic para validação de requests/responses.
"""
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from uuid import UUID


class SourceTargetSchema(BaseModel):
    """Schema para source/target."""
    domain: str = Field(..., description="Domain: 'crypto' ou 'finance'")
    adapter: str = Field(..., description="Adapter type: 'pi_network', 'pix', etc.")
    
    @validator('domain')
    def validate_domain(cls, v):
        if v not in ['crypto', 'finance']:
            raise ValueError("domain must be 'crypto' or 'finance'")
        return v


class BridgeFlowCreateRequest(BaseModel):
    """Request para criar um flow."""
    source: SourceTargetSchema
    target: SourceTargetSchema
    asset: str = Field(..., description="Asset code: 'PI', 'ETH', etc.")
    amount: Decimal = Field(..., gt=0, description="Amount to bridge")
    callback_url: Optional[HttpUrl] = Field(None, description="Webhook callback URL")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    source_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    target_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class FlowEventResponse(BaseModel):
    """Response de evento."""
    event_id: UUID
    event_type: str
    from_state: Optional[str]
    to_state: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True


class BridgeFlowResponse(BaseModel):
    """Response de flow."""
    flow_id: UUID
    status: str
    source: Dict[str, Any]
    target: Dict[str, Any]
    asset: str
    amount: str
    result: Dict[str, Any]
    error_code: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    links: Dict[str, str]
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Response de erro padronizado."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class WebhookPayload(BaseModel):
    """Payload de webhook."""
    event: str
    flow_id: str
    status: str
    asset: str
    amount: str
    result: Dict[str, Any]
    error_code: Optional[str]
    error_message: Optional[str]
    timestamp: str
    metadata: Dict[str, Any]
