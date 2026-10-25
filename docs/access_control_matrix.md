# AgriLens Role-Based Access Control Matrix

**Platform:** AgriLens &bull; See Agriculture Through Data  
**Event:** 2026 NISR Big Data Hackathon &bull; Track 1: Agricultural Productivity  
**Document Version:** 2.0 &bull; Complete System Matrix (Notifications, ML, Workflows & Security)  

---

## 1. Access Control Matrix by Institutional Role

| Module / Route | Anonymous / Public | District Officer | Data Entry Officer | Quality Reviewer | National Officer / Policy Maker | Agricultural Analyst | NISR Data Manager | Administrator |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Public Portal & Map (`/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **National Dashboard (`/dashboard/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **Yield Gap Analytics (`/indicators/productivity/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **Decision Support Hub (`/decision-support/`)** | &cross; | Scoped Read | &cross; | Read | Read | Read | Read | Admin |
| **Actionable Recommendations (`/decision-support/recommendations/`)** | &cross; | Scoped Read | &cross; | Verify/Review | Read | Read | Read | Admin |
| **National Report (`/dashboard/reports/national/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **District Dossier (`/dashboard/reports/district/`)** | Public Read | **Scoped Read** | Scoped Read | Read | Read | Read | Read | Read |
| **Report Center & Exports (`/reports/`)** | &cross; | Scoped Export | &cross; | Export | Export | Export | Export | Admin |
| **Crops & Seasons (`/agriculture/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **Districts & Mapping (`/geography/`)** | Public Read | **Scoped Read** | Read | Read | Read | Read | Read | Read |
| **Seasonal Surveys (`/surveys/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **Farmers & Coops (`/farmers/`)** | &cross; | **Scoped Read** | Scoped Read | Read | Read | Read | Read | Read |
| **Inputs & Subsidies (`/inputs/`)** | &cross; | **Scoped Read** | Scoped Read | Read | Read | Read | Read | Read |
| **Commodity Markets (`/markets/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **Market Price Submission (`/markets/prices/create/`)** | &cross; | Scoped Create | Create | &cross; | &cross; | Create | Create | Admin |
| **Data Lineage Hub (`/data-management/`)** | &cross; | &cross; | &cross; | &cross; | &cross; | Read | Read | Admin |
| **Register Data Source (`/data-management/sources/new/`)**| &cross; | &cross; | &cross; | &cross; | &cross; | Create | Create | Admin |
| **Manual Registry (`/data-management/manual/`)** | &cross; | **Scoped Read** | Read (Self) | Read | Read | Read | Read | Admin |
| **Submit Observation (`/data-management/manual/new/`)** | &cross; | **Scoped Create**| Create | &cross; | &cross; | Create | Create | Admin |
| **Review / Approve Entry (`/data-management/manual/<pk>/review/`)**| &cross; | &cross; | &cross; | **Approve** (No Self)| Approve (No Self)| Approve (No Self)| Approve (No Self)| Admin |
| **Notification Center (`/notifications/`)** | &cross; | Read (Self) | Read (Self) | Read (Self) | Read (Self) | Read (Self) | Read (Self) | Read (Self) |
| **Notification Preferences (`/notifications/preferences/`)**| &cross; | Update (Self)| Update (Self)| Update (Self)| Update (Self)| Update (Self)| Update (Self)| Update (Self)|
| **Admin Announcements & Email Log (`/notifications/admin/`)**| &cross; | &cross; | &cross; | &cross; | &cross; | &cross; | &cross; | **Full Admin** |
| **User Management (`/accounts/users/`)** | &cross; | &cross; | &cross; | &cross; | &cross; | &cross; | &cross; | **Full Admin** |
| **Register Officer (`/accounts/users/new/`)** | &cross; | &cross; | &cross; | &cross; | &cross; | &cross; | &cross; | **Full Admin** |
| **Security Audit Trail (`/accounts/audit-log/`)** | &cross; | &cross; | &cross; | &cross; | &cross; | &cross; | &cross; | **Full Admin** |
| **ML Inference API (`/api/v1/ml/predict-yield/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **ML Scenario Simulation (`/api/v1/ml/simulate-scenario/`)**| Read | Read | Read | Read | Read | Read | Read | Read |
| **ML District Clusters (`/api/v1/ml/district-clusters/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **ML Retraining Trigger (`/api/v1/ml/train/`)** | &cross; | &cross; | &cross; | &cross; | &cross; | &cross; | Trigger | **Full Admin** |

---

## 2. Geographic Jurisdiction Scoping Matrix

District Officers (`DISTRICT_OFFICER`) and regional agronomists are strictly confined to their assigned administrative districts:

```text
┌───────────────────────────┬────────────────────────────────────────────────────────┐
│ Platform Component        │ Enforcement Mechanism                                  │
├───────────────────────────┼────────────────────────────────────────────────────────┤
│ District Dossier Report   │ GET /dashboard/reports/district/<id>/                  │
│                           │ Scoped dropdown; HTTP 403 on unassigned district       │
├───────────────────────────┼────────────────────────────────────────────────────────┤
│ Administrative Geography  │ GET /geography/districts/<id>/                         │
│                           │ Scoped list; HTTP 403 on unassigned district detail    │
├───────────────────────────┼────────────────────────────────────────────────────────┤
│ Manual Registry List      │ GET /data-management/manual/                           │
│                           │ Scoped via scope_queryset_by_geography(district)       │
├───────────────────────────┼────────────────────────────────────────────────────────┤
│ Manual Observation Submit │ POST /data-management/manual/new/                      │
│                           │ Validated via can_access_district(district_id)         │
├───────────────────────────┼────────────────────────────────────────────────────────┤
│ Manual Observation Detail │ GET /data-management/manual/<pk>/                      │
│                           │ HTTP 403 if entry.district_id not in assigned_districts│
├───────────────────────────┼────────────────────────────────────────────────────────┤
│ Decision Support Dossiers │ GET /decision-support/recommendations/                 │
│                           │ Filtered to recommendations within assigned district   │
├───────────────────────────┼────────────────────────────────────────────────────────┤
│ REST ViewSets (DRF)       │ GET /api/districts/, GET /api/prices/                  │
│                           │ Scoped queryset filtered by assigned_districts         │
└───────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 3. Separation of Duties & Security Safeguards

1. **Separation of Data Entry and Approval:** An officer who inputs a manual agricultural observation is strictly prohibited from approving that same record (`Conflict of Interest Guard`), even if they hold the `REVIEWER` or `ADMIN` role.
2. **Administrator Self-Lockout Guard:** Administrators cannot deactivate their own active account or strip their own administrative permissions.
3. **Automated Tokenized Onboarding:** Newly provisioned accounts receive a single-use cryptographically signed token via transactional email (`apps.notifications.tasks`) to set their password.
4. **Active Session Preservation:** Self-service password change preserves the user's active session while broadcasting security notifications across in-app and email channels.
5. **Immutable Audit Trail:** All approval, rejection, role change, geographic assignment, and notification retry operations emit append-only `AuditLog` records containing client IP, actor user, and sanitized metadata.

---

## ⚖️ Intellectual Property, License & Usage Policy

> ### ⚠️ STRICT RESTRICTED USE NOTICE
> **All Rights Reserved © 2026 AgriLens Development Team.**
>
> 1. **Non-Commercial & No Personal Profit:**  
>    No individual, entity, or third party is permitted to use, copy, reproduce, monetize, sub-license, or exploit any portion of this codebase, architecture, machine learning models, algorithms, or visual designs for commercial purposes, revenue generation, or personal financial profit under any circumstances.
>
> 2. **Public Hackathon Visibility Disclaimer:**  
>    Although this repository is publicly accessible solely for the purpose of evaluation, review, and judging during the **2026 NISR Big Data Hackathon (Track 1: Agricultural Productivity)**, public availability does **NOT** constitute an open-source license, public domain dedication, or waiver of intellectual property rights.
>
> 3. **Prohibition of Modifications & Derivative Works:**  
>    Any unauthorized modification, alteration, redistribution, fork, decompilation, reverse-engineering, or derivation of this codebase or its underlying assets is strictly prohibited.
>
> 4. **Exclusive Authorization for NISR:**  
>    Operational utilization, institutional adoption, data integration, and platform deployment are **exclusively and solely permitted for the National Institute of Statistics of Rwanda (NISR)** and its officially designated national agricultural partners.
