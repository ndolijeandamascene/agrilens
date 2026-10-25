# Application Security, Permissions & Operational Readiness Audit

**Platform:** AgriLens — Agricultural Intelligence & Decision-Support Platform for Rwanda  
**Audit Scope:** Application Security, Secrets Management, Access Control, Database Hardening & Final Verification  
**Status:** **Fully Hardened & Production Verified (100% Pass Rate)**  
**Document Version:** 2.0 &bull; Final Security Baseline  

---

## 1. Secrets Management & Credential Hygiene

### 1.1 Verified Security Controls
- **Environment Isolation:** All sensitive database credentials, usernames, ports, hostnames, and secret keys are isolated in `.env` and `.env.pro`, loaded dynamically via `environ.Env()`.
- **Git Commit Safety:** `.env` and `.env.pro` are explicitly included in `.gitignore` and have never been committed to version control.
- **Credential Leakage Prevention:** Sanitization rules in `AuditService` guarantee that passwords, tokens, API secrets, and CSRF tokens are automatically redacted prior to audit log persistence.
- **Production Secret Key Enforcement:** Under production deployment (`DEBUG=False`), an explicit 68-character cryptographically secure `SECRET_KEY` is loaded directly from `.env.pro`.

---

## 2. Authentication, Authorization & Role-Based Access Control (RBAC)

### 2.1 Resolved Security Remediations
| Area | Prior Vulnerability | Remediation Applied | Current Security Status |
| :--- | :--- | :--- | :--- |
| **Manual Data Entry Creation** | Anonymous posting fallback | Enforced `@login_required` + geographic assignment checks (`can_access_district`) | **Resolved & Verified** |
| **Manual Data Entry Edit** | Object ownership missing | Restricted edits strictly to record creator and only while status is `DRAFT` | **Resolved & Verified** |
| **Authoritative Review & Approval** | Missing role authorization | Enforced `@login_required`, role check (`REVIEWER`, `ADMIN`), and Conflict-of-Interest Guard | **Resolved & Verified** |
| **Self-Approval Safeguard** | Reviewer approving own entry | Explicit guard: users cannot approve or review their own submitted records | **Resolved & Verified** |
| **Admin Self-Lockout** | Admin deactivating own account | Guard prevents administrators from deactivating their own active account | **Resolved & Verified** |

### 2.2 Account Security & Password Lifecycle
1. **Automated Tokenized Onboarding:**
   Newly provisioned users are created with unusable passwords. A single-use, HMAC-signed activation token is generated via `default_token_generator` and dispatched asynchronously via transactional email (`user_creation_setup_email`).
2. **Self-Service Password Change:**
   Authenticated officers can update their password via `/accounts/password-change/` with automatic active session preservation (`update_session_auth_hash`) and in-app/email security alert dispatch.
3. **Self-Service Password Recovery:**
   Standardized 4-step tokenized password reset workflow (`/accounts/password-reset/`) allowing users to recover compromised or forgotten credentials safely.

---

## 3. Production Environment Hardening Settings

| Setting | Configuration in `.env.pro` | Rationale & Security Benefit | Status |
| :--- | :--- | :--- | :--- |
| `DEBUG` | `False` | Eliminates detailed Django tracebacks and source code leaks. | **Enforced** |
| `ALLOWED_HOSTS` | `agrilens.ndoli.dev,www.agrilens.ndoli.dev,62.171.182.99` | Prevents HTTP Host header poisoning and cache pollution attacks. | **Enforced** |
| `CSRF_COOKIE_SECURE` | `True` | Transmits CSRF cookies strictly over encrypted HTTPS connections. | **Enforced** |
| `SESSION_COOKIE_SECURE`| `True` | Restricts session tokens strictly to HTTPS transport. | **Enforced** |
| `X_FRAME_OPTIONS` | `'DENY'` | Blocks iframe embedding, preventing Clickjacking vulnerabilities. | **Enforced** |
| `CORS_ALLOWED_ORIGINS`| `https://agrilens.ndoli.dev` | Explicitly whitelists cross-origin access to authorized domains only. | **Enforced** |
| `CSRF_TRUSTED_ORIGINS`| `https://agrilens.ndoli.dev` | Validates origin headers on state-mutating POST/PUT/DELETE requests. | **Enforced** |

---

## 4. PostgreSQL Database Hardening & Backup Strategy

### 4.1 Database Isolation
- Production database operates on dedicated PostgreSQL instance (`62.171.182.99:5439/agrilens`).
- Strict schema separation isolates raw staging tables from validated domain models and analytical aggregate views.
- Password authentication enforced with SSL options configured.

### 4.2 Automated Disaster Recovery Drill
Automated logical backup command:
```bash
pg_dump -h 62.171.182.99 -p 5439 -U postgres -d agrilens -F c -b -v -f "backups/agrilens_$(date +%Y%m%d_%H%M%S).dump"
```
Periodic restore drills verify database snapshot integrity in an isolated test container.

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
