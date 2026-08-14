"""Domain and validation models for enterprise investigation entities."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CustomerModel(BaseModel):
    """Customer entity schema."""

    model_config = ConfigDict(from_attributes=True)

    customer_id: str = Field(..., description="Unique customer identifier (e.g. CUST-0001)")
    segment: str = Field(..., description="Business segment: enterprise, mid_market, smb, startup")
    region: str = Field(..., description="Geographic region: US-East, US-West, EU-Central, APAC")
    signup_date: date = Field(..., description="Date of initial customer signup")
    plan: str = Field(..., description="Subscription plan level: starter, pro, enterprise")


class SubscriptionModel(BaseModel):
    """Subscription entity schema."""

    model_config = ConfigDict(from_attributes=True)

    subscription_id: str = Field(..., description="Unique subscription ID (e.g. SUB-0001)")
    customer_id: str = Field(..., description="Foreign key reference to customer")
    start_date: date = Field(..., description="Subscription start date")
    status: str = Field(..., description="Status: active, cancelled, paused")
    cancellation_date: Optional[date] = Field(None, description="Date subscription was cancelled, if applicable")
    cancellation_reason: Optional[str] = Field(None, description="Reported reason for cancellation")


class SupportTicketModel(BaseModel):
    """Support ticket entity schema."""

    model_config = ConfigDict(from_attributes=True)

    ticket_id: str = Field(..., description="Unique support ticket ID (e.g. TCKT-0001)")
    customer_id: str = Field(..., description="Foreign key reference to customer")
    created_at: datetime = Field(..., description="Timestamp when ticket was filed")
    resolved_at: Optional[datetime] = Field(None, description="Timestamp when ticket was resolved")
    priority: str = Field(..., description="Priority: low, medium, high, urgent")
    category: str = Field(..., description="Category: billing, account_access, technical, feature_request")
    status: str = Field(..., description="Ticket status: open, resolved, escalated")


class BillingEventModel(BaseModel):
    """Billing event entity schema."""

    model_config = ConfigDict(from_attributes=True)

    billing_event_id: str = Field(..., description="Unique billing event ID (e.g. BILL-0001)")
    customer_id: str = Field(..., description="Foreign key reference to customer")
    event_date: date = Field(..., description="Date of billing event")
    event_type: str = Field(..., description="Event type: subscription_charge, invoice, refund, retry")
    amount: float = Field(..., description="Transaction amount in USD")
    status: str = Field(..., description="Payment status: success, failed, pending")


class ProductIncidentModel(BaseModel):
    """Product incident entity schema."""

    model_config = ConfigDict(from_attributes=True)

    incident_id: str = Field(..., description="Unique incident ID (e.g. INC-0001)")
    incident_date: date = Field(..., description="Date incident occurred")
    severity: str = Field(..., description="Severity level: P1, P2, P3, P4")
    service: str = Field(..., description="Impacted microservice or system")
    description: str = Field(..., description="Incident description and impact summary")


class ReleaseEventModel(BaseModel):
    """Release event entity schema."""

    model_config = ConfigDict(from_attributes=True)

    release_id: str = Field(..., description="Unique release ID (e.g. REL-0001)")
    release_date: date = Field(..., description="Date of software release deployment")
    service: str = Field(..., description="Target service/component deployed")
    version: str = Field(..., description="Semantic version string (e.g. v2.4.0)")
    change_type: str = Field(..., description="Type of change: feature, bugfix, refactor, hotfix")
