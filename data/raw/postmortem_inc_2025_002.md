# Incident Postmortem: INC-2025-002

**Date:** 2025-09-08  
**Severity:** P1 (Critical)  
**Impacted Service:** `billing-gateway`  
**Author:** Payments Engineering Team  

---

## 1. Summary
On September 5, 2025, Customer Operations raised alarms regarding multiple enterprise customer accounts being locked out and marked as delinquent. Investigation revealed that the deployment of `billing-gateway` version `v2.4.0` on September 2, 2025 contained a regression in the asynchronous webhook signature reconciliation logic. 

As a result, valid automated recurring payment confirmations from EU and US-East banks were dropped, causing billing records to register as `failed`. The automated subscription lifecycle worker subsequently sent payment failure notices and restricted account access for affected organizations.

---

## 2. Root Cause
A refactored webhook handler introduced in `v2.4.0` did not properly account for 3DS token renewal callbacks, resulting in dropped confirmation events and a 35% false-failure rate for recurring charges.

---

## 3. Remediation
- Hotfix release `v2.4.1` deployed to rollback legacy webhook handler logic.
- Manual account unlock scripts executed for impacted customer IDs.
- Support team notified to prioritize billing dispute tickets.
