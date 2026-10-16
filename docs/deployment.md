# AgriLens Production Deployment Guide

**Platform:** AgriLens — Agricultural Intelligence & Decision-Support Platform for Rwanda  
**Domain:** `https://agrilens.ndoli.dev` (and `https://www.agrilens.ndoli.dev`)  
**Server Host IP:** `62.171.182.99`  
**Docker Image:** `ndoli/agrilens:latest`  
**Database:** PostgreSQL 16 on `62.171.182.99:5439/agrilens`

---

## 1. Architecture Overview

```
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
                    │  WhiteNoise)      │
                    └─────────┬─────────┘
                              │ Port 5439
                    ┌─────────▼─────────┐
                    │ PostgreSQL Server │
                    │ agrilens_db       │
                    └───────────────────┘
```

---

## 2. Production Environment File (`.env.pro`)

The `.env.pro` file contains production secrets and settings. It is excluded from version control via `.gitignore`.

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
| `DOCKER_IMAGE` | Canonical image tag | `ndoli/agrilens:latest` |

---

## 3. Building and Publishing the Docker Image

### Step 3.1: Build Docker Image Locally
```bash
docker build -t ndoli/agrilens:latest .
```

### Step 3.2: Verify the Image Locally
```bash
docker run --rm -p 8000:8000 --env-file .env.pro ndoli/agrilens:latest
```
Check health endpoint in browser or terminal:
```bash
curl http://localhost:8000/health/
# Expected: OK
```

### Step 3.3: Push to Docker Hub
```bash
docker push ndoli/agrilens:latest
```

---

## 4. Deploying via Easypanel

1. Log into your **Easypanel** dashboard at `http://62.171.182.99` (or custom admin domain).
2. Create or navigate to your project (e.g. `agrilens`).
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
   - Paste the contents of `.env.pro`.
7. Under **Volumes / Persistent Storage** (optional for media uploads):
   - Mount `/app/media` to a named volume.
8. Click **Deploy**.

---

## 5. Deploying via Docker Compose (VPS CLI)

If deploying directly on the VPS command line:

```bash
# Clone the repository on the server
git clone <repo-url> /opt/agrilens
cd /opt/agrilens

# Create or copy .env.pro securely
nano .env.pro

# Start the stack in background
docker compose up -d

# Verify logs
docker compose logs -f web
```

---

## 6. Post-Deployment Maintenance Commands

Run migrations or create superuser directly inside the container:

```bash
# Run migrations
docker exec -it agrilens-web python manage.py migrate

# Create admin superuser
docker exec -it agrilens-web python manage.py createsuperuser

# Collect static files manually if needed
docker exec -it agrilens-web python manage.py collectstatic --noinput

# Run sanity check
docker exec -it agrilens-web python manage.py check --deploy
```
