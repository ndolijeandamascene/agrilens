# AgriLens Role-Based Access Control Matrix

**Platform:** AgriLens &bull; See Agriculture Through Data  
**Event:** 2026 NISR Big Data Hackathon &bull; Track 1: Agricultural Productivity  
**Milestone:** Milestone 4: Dashboard Navigation, User Management &amp; Role-Based Access Control  
**Document Version:** 1.0 &bull; October 2026  

---

## 1. Access Control Matrix by Institutional Role

| Module / Route | Anonymous / Public | District Officer | Data Entry Officer | Quality Reviewer | National Officer / Policy Maker | Agricultural Analyst | NISR Data Manager | Administrator |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Public Portal &amp; Map (`/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **National Dashboard (`/dashboard/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **Yield Gap Analytics (`/indicators/productivity/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **National Report (`/dashboard/reports/national/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **District Dossier (`/dashboard/reports/district/`)** | Public Read | **Scoped Read** | Scoped Read | Read | Read | Read | Read | Read |
| **Crops &amp; Seasons (`/agriculture/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **Districts &amp; Mapping (`/geography/`)** | Public Read | **Scoped Read** | Read | Read | Read | Read | Read | Read |
| **Seasonal Surveys (`/surveys/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **Farmers &amp; Coops (`/farmers/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **Inputs &amp; Subsidies (`/inputs/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **Commodity Markets (`/markets/`)** | Read | Read | Read | Read | Read | Read | Read | Read |
| **Developer API (`/api/`)** | Public Read | **Scoped Read** | Read | Read | Read | Read | Read | Read |
| **Data Lineage Hub (`/data-management/`)** | &cross; | &cross; | &cross; | &cross; | &cross; | Read | Read | Admin |
| **Register Data Source (`/data-management/sources/new/`)**| &cross; | &cross; | &cross; | &cross; | &cross; | Create | Create | Admin |
| **Manual Registry (`/data-management/manual/`)** | &cross; | **Scoped Read** | Read (Self) | Read | Read | Read | Read | Admin |
| **Submit Observation (`/data-management/manual/new/`)** | &cross; | **Scoped Create**| Create | &cross; | &cross; | Create | Create | Admin |
| **Review / Approve Entry (`/data-management/manual/<pk>/review/`)**| &cross; | &cross; | &cross; | **Approve** (No Self)| Approve (No Self)| Approve (No Self)| Approve (No Self)| Admin |
| **User Management (`/accounts/users/`)** | &cross; | &cross; | &cross; | &cross; | &cross; | &cross; | &cross; | **Full Admin** |
| **Register Officer (`/accounts/users/new/`)** | &cross; | &cross; | &cross; | &cross; | &cross; | &cross; | &cross; | **Full Admin** |
| **Security Audit Trail (`/accounts/audit-log/`)** | &cross; | &cross; | &cross; | &cross; | &cross; | &cross; | &cross; | **Full Admin** |

---

## 2. Geographic Jurisdiction Scoping Matrix

District Officers (`DISTRICT_OFFICER`) are strictly confined to their provisioned administrative districts. The table below illustrates the enforcement mechanism across platform layers:

```
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
│ REST ViewSets (DRF)       │ GET /api/districts/, GET /api/prices/                  │
│                           │ Scoped queryset filtered by assigned_districts         │
└───────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 3. Separation of Duties &amp; Self-Approval Safeguards

To maintain data integrity and regulatory auditability:
1. **Separation of Data Entry and Approval:** An officer who enters a manual agricultural observation is strictly prohibited from approving that same record, even if they hold the `REVIEWER` role.
2. **Administrator Self-Lockout:** Administrators cannot deactivate their own account or strip their own administrative privileges.
3. **Immutable Audit Trail:** All approval, rejection, role change, and geographic assignment operations emit append-only `AuditLog` records containing client IP, actor user, and sanitized action metadata.
