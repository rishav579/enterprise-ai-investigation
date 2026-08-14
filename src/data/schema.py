"""SQLAlchemy relational schema definitions for enterprise investigation dataset."""

from sqlalchemy import (
    Column,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Customer(Base):
    """Customers table."""

    __tablename__ = "customers"

    customer_id = Column(String(32), primary_key=True)
    segment = Column(String(32), nullable=False)  # enterprise, mid_market, smb, startup
    region = Column(String(32), nullable=False)   # US-East, US-West, EU-Central, APAC
    signup_date = Column(Date, nullable=False)
    plan = Column(String(32), nullable=False)     # starter, pro, enterprise

    # Relationships
    subscriptions = relationship("Subscription", back_populates="customer", cascade="all, delete-orphan")
    support_tickets = relationship("SupportTicket", back_populates="customer", cascade="all, delete-orphan")
    billing_events = relationship("BillingEvent", back_populates="customer", cascade="all, delete-orphan")


class Subscription(Base):
    """Subscriptions table."""

    __tablename__ = "subscriptions"

    subscription_id = Column(String(32), primary_key=True)
    customer_id = Column(String(32), ForeignKey("customers.customer_id"), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    status = Column(String(32), nullable=False)  # active, cancelled, paused
    cancellation_date = Column(Date, nullable=True, index=True)
    cancellation_reason = Column(String(128), nullable=True)

    customer = relationship("Customer", back_populates="subscriptions")


class SupportTicket(Base):
    """Support tickets table."""

    __tablename__ = "support_tickets"

    ticket_id = Column(String(32), primary_key=True)
    customer_id = Column(String(32), ForeignKey("customers.customer_id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    priority = Column(String(16), nullable=False)  # low, medium, high, urgent
    category = Column(String(32), nullable=False, index=True)  # billing, account_access, technical, feature_request
    status = Column(String(32), nullable=False)    # open, resolved, escalated

    customer = relationship("Customer", back_populates="support_tickets")


class BillingEvent(Base):
    """Billing events table."""

    __tablename__ = "billing_events"

    billing_event_id = Column(String(32), primary_key=True)
    customer_id = Column(String(32), ForeignKey("customers.customer_id"), nullable=False, index=True)
    event_date = Column(Date, nullable=False, index=True)
    event_type = Column(String(32), nullable=False)  # subscription_charge, invoice, refund, retry
    amount = Column(Float, nullable=False)
    status = Column(String(32), nullable=False, index=True)  # success, failed, pending

    customer = relationship("Customer", back_populates="billing_events")


class ProductIncident(Base):
    """Product incidents table."""

    __tablename__ = "product_incidents"

    incident_id = Column(String(32), primary_key=True)
    incident_date = Column(Date, nullable=False, index=True)
    severity = Column(String(16), nullable=False)  # P1, P2, P3, P4
    service = Column(String(64), nullable=False, index=True)
    description = Column(Text, nullable=False)


class ReleaseEvent(Base):
    """Software release events table."""

    __tablename__ = "release_events"

    release_id = Column(String(32), primary_key=True)
    release_date = Column(Date, nullable=False, index=True)
    service = Column(String(64), nullable=False, index=True)
    version = Column(String(32), nullable=False)
    change_type = Column(String(32), nullable=False)  # feature, bugfix, refactor, hotfix


# Composite index definitions for optimized analytical lookups
Index("idx_subscriptions_status_date", Subscription.status, Subscription.cancellation_date)
Index("idx_billing_events_status_date", BillingEvent.status, BillingEvent.event_date)
Index("idx_tickets_category_created", SupportTicket.category, SupportTicket.created_at)
