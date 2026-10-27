# AgriLens Production Deployment Guide

**Platform:** AgriLens — Agricultural Intelligence & Decision-Support Platform for Rwanda  
**Domain:** `https://agrilens.ndoli.dev` (and `https://www.agrilens.ndoli.dev`)  
**Server Host IP:** `62.171.182.99`  
**Docker Image:** `ndoli/agrilens:latest`  
**Database:** PostgreSQL 16 on `62.171.182.99:5439/agrilens`  
**Document Version:** 2.0 &bull; Verified Production Deployment  

---

## 🚀 Live Evaluation Credentials

For the **2026 NISR Big Data Hackathon Jury & Technical Reviewers**:

| Parameter | Value |
| :--- | :--- |
| **Live Portal URL** | **[https://agrilens.ndoli.dev](https://agrilens.ndoli.dev)** |
| **Administrative Username** | `admin` |
| **Password** | `AgriLens2026!` |
| **Access Clearance** | `System Administrator (Full Superuser)` |
| **Request Full `.env` File** | Email: **[ndolijeandamascene@gmail.com](mailto:ndolijeandamascene@gmail.com)** &bull; WhatsApp: **[+250 789 312 765](https://wa.me/250789312765)** |

---

## 1. Architecture Overview

```text
                      [ Client Browser ]
                              │
                    HTTPS (agrilens.ndoli.dev)
                              │
                    ┌─────────▼─────────┐
                    │ DNS: Name.com     │
                    │ A: 62.171.182.99  │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Reverse Proxy     │
                    │ (Easypanel/Traefik│
                    │  SSL Termination) │
                    └─────────┬─────────┘
                              │ Port 8000 (HTTP)
                    ┌─────────▼─────────┐
                    │ Docker Container  │
                    │ ndoli/agrilens    │
                    │ (Gunicorn +       │
                    │  WhiteNoise +     │
                    │  Async Workers)   │
                    └─────────┬─────────┘
                              │ Port 5439
                    ┌─────────▼─────────┐
                    │ PostgreSQL Server │
                    │ agrilens_db       │
                    └───────────────────┘
```

---

## 2. Production Environment File (`.env`)

The `.env` file contains production secrets and settings. It is excluded from version control via `.gitignore`.

| Environment Variable | Description | Production Value |
| :--- | :--- | :--- |
| `DEBUG` | Disables debug mode and tracebacks | `False` |
| `SECRET_KEY` | Cryptographic secret for sessions and tokens | *Cryptographically secure 68-char token* |
| `ALLOWED_HOSTS` | Whitelisted HTTP Host headers | `agrilens.ndoli.dev,www.agrilens.ndoli.dev,62.171.182.99,localhost,127.0.0.1,web` |
| `CSRF_TRUSTED_ORIGINS`| Whitelisted HTTPS origins for POST requests | `https://agrilens.ndoli.dev,https://www.agrilens.ndoli.dev,http://agrilens.ndoli.dev,http://62.171.182.99` |
| `CORS_ALLOWED_ORIGINS`| Allowed origins for frontend API requests | `https://agrilens.ndoli.dev,https://www.agrilens.ndoli.dev` |
| `SECURE_SSL_REDIRECT` | Redirect HTTP to HTTPS in Django | `False` *(Handled automatically by reverse proxy)* |
| `DATABASE_URL` | Remote PostgreSQL connection string | `postgres://postgres:agrilens123!@62.171.182.99:5439/agrilens?sslmode=disable` |
| `TIME_ZONE` | Standard timezone for Rwanda | `Africa/Kigali` |
| `LANGUAGE_CODE` | Application language | `en-us` |
| `PORT` | Container internal listening port | `8000` |
| `WEB_CONCURRENCY` | Gunicorn worker processes | `3` |
| `EMAIL_BACKEND` | Transactional email delivery engine | `django.core.mail.backends.smtp.EmailBackend` |
| `DEFAULT_FROM_EMAIL`| Sender address for notifications | `AgriLens Intelligence <notifications@agrilens.ndoli.dev>` |

---

## 3. Building and Publishing the Docker Image

### Step 3.1: Build Docker Image Locally
```bash
docker build -t ndoli/agrilens:latest .
```

### Step 3.2: Verify the Image Locally
```bash
docker run --rm -p 8000:8000 --env-file .env ndoli/agrilens:latest
```
Check health endpoint in browser or terminal:
```bash
curl http://localhost:8000/health/
# Expected response: OK
```

### Step 3.3: Push to Docker Hub
```bash
docker push ndoli/agrilens:latest
```

---

## 4. Deploying via Easypanel

1. Log into your **Easypanel** dashboard at `http://62.171.182.99` (or custom admin domain).
2. Create or navigate to your project (e.g., `agrilens`).
3. Click **+ Service** -> choose **App**.
4. Configure the service:
   - **Service Name:** `web` or `agrilens`
   - **Source:** Docker Image
   - **Image:** `ndoli/agrilens:latest`
5. Under **Domains**:
   - Add Domain: `agrilens.ndoli.dev`
   - Port: `8000`
   - Enable SSL (Automatic Let's Encrypt certificate).
6. Under **Environment Variables**:
   - Paste the contents of `.env`.
7. Under **Volumes / Persistent Storage**:
   - Mount `/app/media` to a named volume.
8. Click **Deploy**.

---

## 5. Post-Deployment Maintenance Commands

Run migrations, seed data, and verify services directly inside the live container:

```bash
# Run database migrations
docker exec -it agrilens-web python manage.py migrate

# Seed authoritative geography (30 districts, 416 sectors, crops, seasons)
docker exec -it agrilens-web python scripts/seed_geography.py

# Seed market price surveillance data
docker exec -it agrilens-web python manage.py seed_market_surveillance

# Train yield prediction & district clustering models
docker exec -it agrilens-web python manage.py train_ml_models

# Collect static assets
docker exec -it agrilens-web python manage.py collectstatic --noinput

# Run production security checks
docker exec -it agrilens-web python manage.py check --deploy
```

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
