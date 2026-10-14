# AgriLens User Management, Roles &amp; Permissions

**Platform:** AgriLens &bull; See Agriculture Through Data  
**Event:** 2026 NISR Big Data Hackathon &bull; Track 1: Agricultural Productivity  
**Milestone:** Milestone 4: Dashboard Navigation, User Management &amp; Role-Based Access Control  
**Document Version:** 1.0 &bull; October 2026  

---

## 1. Institutional Role Architecture

AgriLens defines seven primary institutional roles structured according to NISR, MINAGRI, and local government hierarchies in Rwanda, plus an unauthenticated Public Visitor tier:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AgriLens Institutional Hierarchy                │
├────────────────────────────────┬───────────────────────────────────────┤
│ Tier 1: System Administration  │ 1. Administrator (ADMIN)              │
├────────────────────────────────┼───────────────────────────────────────┤
│ Tier 2: National Headquarters  │ 2. NISR Data Manager (NISR_DATA_MGR)  │
│                                │ 3. Agricultural Analyst (ANALYST)     │
│                                │ 4. National Officer (NATIONAL_OFFICER)│
├────────────────────────────────┼───────────────────────────────────────┤
│ Tier 3: Decentralized Districts│ 5. District Officer (DISTRICT_OFFICER)│
│                                │ 6. Data Entry Officer (DATA_ENTRY)    │
│                                │ 7. Quality Reviewer (REVIEWER)        │
├────────────────────────────────┼───────────────────────────────────────┤
│ Tier 0: Public Access          │ 8. Public Visitor (Unauthenticated)   │
└────────────────────────────────┴───────────────────────────────────────┘
```

### Role Descriptions &amp; Responsibilities

| Role Identifier | Display Title | Jurisdiction | Primary Responsibilities |
| :--- | :--- | :--- | :--- |
| `ADMIN` | Administrator | National | Full institutional governance, user onboarding, role &amp; geographic assignments, system audit logs. |
| `NISR_DATA_MANAGER`| NISR Data Manager | National | Ingestion pipelines, survey weight auditing, batch reconciliation, QA issue tracking, dynamic data sources. |
| `ANALYST` | Agricultural Analyst | National | Yield gap modeling, indicator analytics, benchmark rankings, crop productivity assessments, report exports. |
| `NATIONAL_OFFICER` | National Agricultural Officer | National | Policy decision-support, national bulletin generation, high-level priority crop monitoring. |
| `DISTRICT_OFFICER` | District Agricultural Officer | District Scoped | District-level performance dossiers, local manual observation submission, sector performance monitoring. |
| `DATA_ENTRY_OFFICER`| Data Entry Officer | Scoped / National | Manual field observation drafting, cooperative receipt capture, project survey submission. |
| `REVIEWER` | Quality Reviewer | Scoped / National | Peer review, verification, and authoritative approval/rejection of manual agricultural records. |
| `PUBLIC` | Public Visitor | Unrestricted Read | Public analytics portal, national priority crop overviews, public interactive Rwanda agricultural map. |

---

## 2. Backward Compatibility with Legacy Roles

To preserve 100% backward compatibility with pre-existing database records, sessions, and tests, legacy role aliases are explicitly mapped to canonical institutional roles in `User.Role`:

```python
class Role(models.TextChoices):
    # Canonical Institutional Roles
    ADMIN = 'ADMIN', 'Administrator'
    NISR_DATA_MANAGER = 'NISR_DATA_MANAGER', 'NISR Data Manager'
    ANALYST = 'ANALYST', 'Agricultural Analyst'
    NATIONAL_OFFICER = 'NATIONAL_OFFICER', 'National Agricultural Officer'
    DISTRICT_OFFICER = 'DISTRICT_OFFICER', 'District Agricultural Officer'
    DATA_ENTRY_OFFICER = 'DATA_ENTRY_OFFICER', 'Data Entry Officer'
    REVIEWER = 'REVIEWER', 'Quality Reviewer'
    PUBLIC = 'PUBLIC', 'Public Visitor'

    # Legacy Backward-Compatibility Aliases
    POLICY_MAKER = 'POLICY_MAKER', 'Policy Maker (Legacy)'
    EXTENSION_OFFICER = 'EXTENSION_OFFICER', 'Extension Officer (Legacy)'
    RESEARCHER = 'RESEARCHER', 'Agricultural Researcher (Legacy)'
```

### Effective Role Equivalency Engine:
- `POLICY_MAKER` &rarr; Inherits permissions of `NATIONAL_OFFICER` and `ANALYST`.
- `EXTENSION_OFFICER` &rarr; Inherits permissions of `DATA_ENTRY_OFFICER`.
- `RESEARCHER` &rarr; Inherits permissions of `ANALYST`.

---

## 3. Server-Side Security Guards

### A. Conflict-of-Interest &amp; Self-Approval Guard (Condition 5)
Officers with reviewer privileges cannot approve their own submissions:
```python
# Self-Approval Conflict of Interest Guard (Milestone 4 Condition 5)
if entry.created_by == request.user and not request.user.is_superuser:
    messages.error(request, "Conflict of Interest Guard: You cannot review or approve your own manual submissions.")
    return redirect('data_management:manual_entry_detail', pk=entry.pk)
```

### B. Administrator Self-Lockout Prevention (Condition 5)
Administrators cannot deactivate their own account or remove their own administrative privileges:
```python
if request.user.pk == officer.pk:
    messages.error(request, "Security Guard: You cannot deactivate your own active administrator account.")
    return redirect('accounts:user_detail', pk=officer.pk)
```

### C. Privilege Escalation Prevention
Non-superusers cannot grant `is_superuser` status or assign roles higher than their own clearance level.

---

## 4. Single-Use Password Setup Workflow (Condition 6)

In strict compliance with Milestone 4 Condition 6, raw passwords are **never** displayed to administrators, returned in HTTP responses, or stored in plaintext:

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Administrator
    participant Sys as AgriLens Core
    actor Officer as New Officer
    
    Admin->>Sys: Submit officer registration (/accounts/users/new/)
    Note over Sys: Creates user shell with unusable password<br/>Generates signed token via default_token_generator
    Sys-->>Admin: Display single-use setup link (copyable)
    Admin->>Officer: Transmit secure link via official agency channel
    Officer->>Sys: Click link (/accounts/users/setup-password/<uidb64>/<token>/)
    Note over Sys: Validates HMAC cryptographic signature & expiry
    Officer->>Sys: Submit new strong password
    Note over Sys: Activates account, sets password, invalidates token
    Sys-->>Officer: Redirect to login with confirmation
```

---

## 5. Security &amp; Audit Trail (`AuditLog`)

Every administrative action, privilege change, password issuance, and manual record approval is permanently recorded in an append-only `AuditLog` table with client IP address, actor ID, target reference, and sanitized JSON details:

```python
AuditService.log(
    action=AuditLog.Action.SUBMISSION_APPROVED,
    actor=request.user,
    target=entry,
    details={'decision': 'approve', 'district': entry.district.name},
    request=request
)
```

Automatic credential sanitization ensures keys such as `password`, `token`, `secret`, and `csrfmiddlewaretoken` are redacted prior to database persistence.
