"""Unit tests for Pydantic domain models."""

from datetime import date, datetime
import pytest
from pydantic import ValidationError

from src.models import (
    CustomerModel,
    SubscriptionModel,
    SupportTicketModel,
    BillingEventModel,
    ProductIncidentModel,
    ReleaseEventModel,
)


def test_customer_model_valid():
    """Test valid Customer model creation."""
    customer = CustomerModel(
        customer_id="CUST-0001",
        segment="enterprise",
        region="US-East",
        signup_date=date(2024, 1, 15),
        plan="enterprise",
    )
    assert customer.customer_id == "CUST-0001"
    assert customer.segment == "enterprise"
    assert customer.plan == "enterprise"


def test_subscription_model_active_and_cancelled():
    """Test active and cancelled subscription structures."""
    active_sub = SubscriptionModel(
        subscription_id="SUB-0001",
        customer_id="CUST-0001",
        start_date=date(2024, 1, 15),
        status="active",
    )
    assert active_sub.status == "active"
    assert active_sub.cancellation_date is None

    cancelled_sub = SubscriptionModel(
        subscription_id="SUB-0002",
        customer_id="CUST-0002",
        start_date=date(2024, 2, 1),
        status="cancelled",
        cancellation_date=date(2025, 9, 10),
        cancellation_reason="payment_issue",
    )
    assert cancelled_sub.status == "cancelled"
    assert cancelled_sub.cancellation_date == date(2025, 9, 10)


def test_support_ticket_model():
    """Test SupportTicket model validation."""
    ticket = SupportTicketModel(
        ticket_id="TCKT-0001",
        customer_id="CUST-0001",
        created_at=datetime(2025, 9, 5, 10, 30),
        resolved_at=datetime(2025, 9, 7, 14, 0),
        priority="urgent",
        category="billing",
        status="resolved",
    )
    assert ticket.ticket_id == "TCKT-0001"
    assert ticket.priority == "urgent"


def test_billing_event_model():
    """Test BillingEvent model validation."""
    event = BillingEventModel(
        billing_event_id="BILL-0001",
        customer_id="CUST-0001",
        event_date=date(2025, 9, 1),
        event_type="subscription_charge",
        amount=199.0,
        status="failed",
    )
    assert event.amount == 199.0
    assert event.status == "failed"


def test_product_incident_model():
    """Test ProductIncident model validation."""
    incident = ProductIncidentModel(
        incident_id="INC-0001",
        incident_date=date(2025, 9, 5),
        severity="P1",
        service="billing-gateway",
        description="Webhook processor regression.",
    )
    assert incident.severity == "P1"
    assert incident.service == "billing-gateway"


def test_release_event_model():
    """Test ReleaseEvent model validation."""
    release = ReleaseEventModel(
        release_id="REL-0001",
        release_date=date(2025, 9, 2),
        service="billing-gateway",
        version="v2.4.0",
        change_type="refactor",
    )
    assert release.version == "v2.4.0"
    assert release.change_type == "refactor"


def test_model_validation_error_on_missing_required_fields():
    """Test ValidationError when required fields are missing."""
    with pytest.raises(ValidationError):
        CustomerModel(customer_id="CUST-9999")
