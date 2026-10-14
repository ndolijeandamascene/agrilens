# Application Security, Permissions & Operational Readiness Audit

**Platform:** AgriLens — Agricultural Intelligence & Decision-Support Platform for Rwanda  
**Audit Milestone:** Milestone 2  
**Audit Scope:** Application Security, Secrets Management, Access Control, and Database Hardening  

---

## 1. Secrets Management & Credential Hygiene

### 1.1 Findings & Status
- **Environment Variables:** All sensitive database credentials, usernames, ports, and hosts are isolated in `.env` and loaded dynamically via `environ.Env()`.
- **Git Commit Safety:** `.env` is listed in `.gitignore` and has **never been committed** to Git.
- **Credential Leakage Prevention:** Verified that logs, tests, management commands, and documentation redact database connection passwords and internal tokens.
- **Residual Risk:** `config/settings.py` contains a dev fallback for `SECRET_KEY`:
  ```python
  SECRET_KEY = env.str('SECRET_KEY', default='django-insecure-dev-key-agrilens-rwanda-agricultural-platform-2026')
  ```
  **Remediation:** Enforce that in production (`DEBUG=False`), `SECRET_KEY` must be strictly supplied via `.env` without an insecure fallback.

---

## 2. Authentication, Authorization & Role-Based Access Control (RBAC)

### 2.1 Critical Vulnerabilities Discovered
| Area | Vulnerability | Severity | Evidence |
| :--- | :--- | :--- | :--- |
| **Manual Data Entry Creation** | Missing `@login_required` decorator | **High** | In `apps/data_management/views.py`: `manual_entry_create` falls back to `get_default_user()` if unauthenticated, allowing anonymous users to post submissions. |
| **Manual Data Entry Edit** | Missing Object-Level Ownership & Status Check | **High** | In `manual_entry_edit`: Any user can modify any draft submission, regardless of who created it. |
| **Authoritative Review & Approval** | Missing Role-Based Authorization | **Critical** | In `manual_entry_review`: Any user (including anonymous via fallback) can trigger `POST /review/` with `decision=approve` or `decision=reject` without checking if `user.role` is `ADMIN` or `ANALYST`. |

### 2.2 Security Hardening Plan
1. Add `@login_required` to all mutating manual data entry views.
2. Implement role-based permission checks:
   - **Data Entry / Extension Officers (`EXTENSION_OFFICER`, `ANALYST`, `ADMIN`):** Can create and edit their own `DRAFT` submissions.
   - **Reviewers / Authority (`ANALYST`, `ADMIN`, `POLICY_MAKER`):** Authorized to execute `manual_entry_review`.
3. Enforce that ordinary users cannot edit records created by other users unless granted managerial permissions.

---

## 3. Production Environment Hardening Settings

### 3.1 Settings Audit Table
| Setting | Current Configuration | Production Recommendation | Status |
| :--- | :--- | :--- | :--- |
| `DEBUG` | Driven by `.env` (`default=True`) | Must be `False` in production deployment. | **Configured** |
| `ALLOWED_HOSTS` | `['*']` when `DEBUG=False` | **Defect:** Insecure wildcard fallback. Must be explicit domain/IP list. | **Requires Fix** |
| `CSRF_COOKIE_SECURE` | Enabled when `DEBUG=False` | Retain `True` behind HTTPS. | **Configured** |
| `SESSION_COOKIE_SECURE`| Enabled when `DEBUG=False` | Retain `True` behind HTTPS. | **Configured** |
| `X_FRAME_OPTIONS` | `'DENY'` when `DEBUG=False` | Prevents clickjacking. | **Configured** |
| `CORS Configuration` | `corsheaders` installed; no origin list | Add explicit `CORS_ALLOWED_ORIGINS` in `.env`. | **Recommended** |
| `SECURE_SSL_REDIRECT` | Not specified | Add `SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)`. | **Recommended** |

---

## 4. PostgreSQL Database Hardening & Backup Strategy

### 4.1 Database Connectivity
- Database is hosted remotely on `62.171.182.99:5439`.
- **Least-Privilege Recommendation:** The database user should be restricted to `SELECT`, `INSERT`, `UPDATE` on the `agrilens` schema and blocked from dropping public schemas or altering server roles.
- **Firewall Isolation:** If possible, access to port `5439` should be restricted to the application server's static IP via firewall rules rather than public exposure.

### 4.2 Backup & Recovery Protocol
- **Daily Automated Logical Backups:**
  ```bash
  pg_dump -h 62.171.182.99 -p 5439 -U <user> -d agrilens -F c -b -v -f "backups/agrilens_$(date +%Y%m%d_%H%M%S).dump"
  ```
- **Backup Verification & Restore Drill:** Backups must be tested periodically by restoring into an isolated, non-production container to verify snapshot integrity.
