"""Deterministic synthetic enterprise dataset generator and seeder.

This module populates the SQLite database with realistic SaaS operational records
containing a deliberately planted business anomaly (Q3 2025 cancellation spike
caused by a billing gateway regression, support backlog, and subsequent churn).
"""

import random
from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from src.config.settings import settings
from src.data.database import get_db_session, reset_db
from src.data.schema import (
    Customer,
    Subscription,
    SupportTicket,
    BillingEvent,
    ProductIncident,
    ReleaseEvent,
)


def seed_enterprise_database(db_url: Optional[str] = None, seed: Optional[int] = None) -> dict:
    """Seed the database deterministically with synthetic enterprise records.
    
    Returns a dictionary summarizing the count of records inserted per table.
    """
    active_seed = seed if seed is not None else settings.random_seed
    rng = random.Random(active_seed)

    # 1. Reset database tables for clean, idempotent execution
    reset_db(db_url)
    session: Session = get_db_session(db_url)

    try:
        # --- 2. Seed Software Release Events ---
        releases = [
            ReleaseEvent(
                release_id="REL-2025-001",
                release_date=date(2025, 7, 15),
                service="auth-service",
                version="v3.0.0",
                change_type="feature",
            ),
            ReleaseEvent(
                release_id="REL-2025-002",
                release_date=date(2025, 8, 10),
                service="notification-service",
                version="v1.8.2",
                change_type="bugfix",
            ),
            ReleaseEvent(
                release_id="REL-2025-003",
                release_date=date(2025, 9, 2),
                service="billing-gateway",
                version="v2.4.0",
                change_type="refactor",
            ),
            ReleaseEvent(
                release_id="REL-2025-004",
                release_date=date(2025, 9, 20),
                service="web-app",
                version="v4.1.0",
                change_type="feature",
            ),
            ReleaseEvent(
                release_id="REL-2025-005",
                release_date=date(2025, 10, 8),
                service="billing-gateway",
                version="v2.4.1",
                change_type="hotfix",
            ),
        ]
        session.add_all(releases)

        # --- 3. Seed Product Incidents ---
        incidents = [
            ProductIncident(
                incident_id="INC-2025-001",
                incident_date=date(2025, 6, 12),
                severity="P3",
                service="api-gateway",
                description="Intermittent latency observed on APAC edge routing nodes.",
            ),
            ProductIncident(
                incident_id="INC-2025-002",
                incident_date=date(2025, 9, 5),
                severity="P1",
                service="billing-gateway",
                description="Critical regression in payment status webhook processor following v2.4.0 release. Valid customer cards incorrectly marked as declined; automated account lockouts triggered.",
            ),
            ProductIncident(
                incident_id="INC-2025-003",
                incident_date=date(2025, 9, 18),
                severity="P2",
                service="support-portal",
                description="Support ticketing queue overload and delayed webhook ticket dispatch due to unprecedented volume.",
            ),
        ]
        session.add_all(incidents)

        # --- 4. Seed Customers & Subscriptions ---
        segments = ["enterprise", "mid_market", "smb", "startup"]
        segment_weights = [0.20, 0.30, 0.35, 0.15]

        regions = ["US-East", "US-West", "EU-Central", "APAC"]
        region_weights = [0.35, 0.25, 0.30, 0.10]

        plans = ["starter", "pro", "enterprise"]
        plan_weights = [0.40, 0.40, 0.20]

        plan_prices = {"starter": 49.0, "pro": 199.0, "enterprise": 999.0}

        customers = []
        subscriptions = []
        billing_events = []
        support_tickets = []

        total_customers = settings.synthetic_customer_count

        for i in range(1, total_customers + 1):
            cust_id = f"CUST-{i:04d}"
            seg = rng.choices(segments, weights=segment_weights, k=1)[0]
            reg = rng.choices(regions, weights=region_weights, k=1)[0]
            plan = rng.choices(plans, weights=plan_weights, k=1)[0]

            # Signup dates distributed between 2024-01-01 and 2025-06-01
            signup_days_offset = rng.randint(0, 500)
            signup_d = date(2024, 1, 1) + timedelta(days=signup_days_offset)

            customers.append(
                Customer(
                    customer_id=cust_id,
                    segment=seg,
                    region=reg,
                    signup_date=signup_d,
                    plan=plan,
                )
            )

            # Determine subscription status & potential cancellation
            sub_id = f"SUB-{i:04d}"
            
            # Scenario logic:
            # - Baseline churn in Jan-Aug 2025: ~2.5% of total base
            # - Surge churn in Sept 1 - Oct 15 2025:
            #   Customers on 'pro' or 'enterprise' plans in 'EU-Central' or 'US-East' suffer high churn
            #   due to the billing-gateway webhook bug and resulting lockout.
            
            is_vulnerable_cohort = (plan in ["pro", "enterprise"]) and (reg in ["EU-Central", "US-East"])
            roll = rng.random()

            status = "active"
            cancellation_d: Optional[date] = None
            cancellation_reason: Optional[str] = None

            if is_vulnerable_cohort and roll < 0.38:
                # Planted anomaly: Churn between 2025-09-03 and 2025-10-15
                status = "cancelled"
                spike_days_offset = rng.randint(0, 42)
                cancellation_d = date(2025, 9, 3) + timedelta(days=spike_days_offset)
                cancellation_reason = rng.choice([
                    "payment_issue",
                    "unexpected_account_lockout",
                    "support_unresponsive",
                    "billing_discrepancy",
                ])
            elif not is_vulnerable_cohort and roll < 0.08:
                # Normal baseline churn spread across Jan 2025 - Aug 2025
                status = "cancelled"
                baseline_days_offset = rng.randint(0, 240)
                cancellation_d = date(2025, 1, 1) + timedelta(days=baseline_days_offset)
                cancellation_reason = rng.choice([
                    "budget_cuts",
                    "competitor_switch",
                    "no_longer_needed",
                    "project_cancelled",
                ])

            subscriptions.append(
                Subscription(
                    subscription_id=sub_id,
                    customer_id=cust_id,
                    start_date=signup_d,
                    status=status,
                    cancellation_date=cancellation_d,
                    cancellation_reason=cancellation_reason,
                )
            )

            # --- 5. Generate Billing Events for this customer ---
            # Monthly billing cycles from 2025-01-01 to 2025-10-15
            amount = plan_prices[plan]
            for month in range(1, 11):
                charge_date = date(2025, month, min(signup_d.day, 28))
                if charge_date > date(2025, 10, 15):
                    break
                if cancellation_d and charge_date > cancellation_d:
                    break

                bill_id = f"BILL-{cust_id}-{month:02d}"
                bill_status = "success"

                # If during the incident window (Sept 2 - Oct 8) and customer is in vulnerable cohort:
                if month == 9 and is_vulnerable_cohort and rng.random() < 0.65:
                    bill_status = "failed"
                    # Add a retry record shortly after
                    retry_id = f"BILL-{cust_id}-{month:02d}-RETRY"
                    billing_events.append(
                        BillingEvent(
                            billing_event_id=retry_id,
                            customer_id=cust_id,
                            event_date=charge_date + timedelta(days=2),
                            event_type="retry",
                            amount=amount,
                            status="failed" if rng.random() < 0.80 else "success",
                        )
                    )

                billing_events.append(
                    BillingEvent(
                        billing_event_id=bill_id,
                        customer_id=cust_id,
                        event_date=charge_date,
                        event_type="subscription_charge",
                        amount=amount,
                        status=bill_status,
                    )
                )

            # --- 6. Generate Support Tickets for this customer ---
            # Baseline ticket generation
            ticket_counter = 1
            if rng.random() < 0.35:
                ticket_id = f"TCKT-{cust_id}-{ticket_counter}"
                ticket_counter += 1
                cat = rng.choice(["technical", "feature_request", "general_inquiry"])
                t_date = datetime(2025, rng.randint(1, 8), rng.randint(1, 28), rng.randint(8, 17))
                resolved_date = t_date + timedelta(hours=rng.uniform(1.5, 8.0))

                support_tickets.append(
                    SupportTicket(
                        ticket_id=ticket_id,
                        customer_id=cust_id,
                        created_at=t_date,
                        resolved_at=resolved_date,
                        priority=rng.choice(["low", "medium"]),
                        category=cat,
                        status="resolved",
                    )
                )

            # Planted spike in support tickets for customers experiencing the billing failure
            if is_vulnerable_cohort and (status == "cancelled" or rng.random() < 0.50):
                ticket_id = f"TCKT-{cust_id}-{ticket_counter}"
                t_date = datetime(2025, 9, rng.randint(3, 25), rng.randint(8, 19))
                # Severe resolution delay in September (36 to 96 hours)
                resolved_date = t_date + timedelta(hours=rng.uniform(36.0, 96.0))
                is_open = rng.random() < 0.15

                support_tickets.append(
                    SupportTicket(
                        ticket_id=ticket_id,
                        customer_id=cust_id,
                        created_at=t_date,
                        resolved_at=None if is_open else resolved_date,
                        priority="urgent" if plan == "enterprise" else "high",
                        category=rng.choice(["billing", "account_access"]),
                        status="open" if is_open else "resolved",
                    )
                )

        session.add_all(customers)
        session.add_all(subscriptions)
        session.add_all(billing_events)
        session.add_all(support_tickets)

        session.commit()

        counts = {
            "customers": len(customers),
            "subscriptions": len(subscriptions),
            "billing_events": len(billing_events),
            "support_tickets": len(support_tickets),
            "product_incidents": len(incidents),
            "release_events": len(releases),
        }
        return counts

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("[INFO] Seeding enterprise investigation dataset...")
    record_counts = seed_enterprise_database()
    print("[SUCCESS] Seeding completed successfully:")
    for table_name, count in record_counts.items():
        print(f"   - {table_name}: {count} records")
