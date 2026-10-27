# AgriLens Production Deployment & Server Verification Guide

**Target Environment**: Linux Ubuntu/Debian / Docker / Easypanel / Standalone VM  
**Target Domain**: `agrilens.ndoli.dev` (or Server IP `62.171.182.99`)  
**Production Image**: `ndoli/agrilens:latest`  
**Hackathon Track**: 2026 NISR Big Data Hackathon – Track 1: Agricultural Productivity  

---

## 1. System Architecture Overview

```mermaid
flowchart TD
    User([Public Visitor / Citizen]) -->|Visits / or /reports/| WebUI[Public Base Template]
    Officer([Institutional Officer: Admin/Analyst/District]) -->|Authenticated Session| WebUI
    
    WebUI --> ChatWidget[Floating AI Chatbot Widget]
    ChatWidget -->|POST /api/v1/assistant/query/| API[Assistant Query API View]
    
    API --> Clearance[AgronomicPromptBuilder: Resolve Role Clearance]
    Clearance -->|Anonymous| PublicClearance[PUBLIC_VISITOR: Published Aggregates Only]
    Clearance -->|Authenticated| InstitutionalClearance[INSTITUTIONAL_CLEARANCE: Tactical & Operational]
    
    API --> ORM[Grounded ORM Engine: 23,833 NISR Records]
    ORM --> DeterministicFacts[Authoritative Statistical Calculations]
    
    DeterministicFacts --> QwenRuntime[In-Process Qwen 2.5 3B: llama-cpp-python]
    QwenRuntime -->|Role System Prompt + ChatML| SynthesizedResponse[Enriched Role-Aware Agronomic Analysis]
    SynthesizedResponse --> Log[AssistantQueryLog: Audit Trail]
    Log --> ResponsePayload[JSON Response: Grounded Facts + Qwen Synthesis]
```

### Key Production Highlights:
1. **Zero External Daemon Dependencies**: No Ollama service, no cloud API keys, zero network latency to third parties.
2. **In-Process Inference**: Uses `llama-cpp-python` with `use_mmap=True` to memory-map the 2.1 GB quantized GGUF model directly in RAM.
3. **Dual Grounding & Zero Hallucination**: Authoritative NISR survey metrics are computed first; Qwen 2.5 3B contextually enriches the numbers without altering them.
4. **Graceful Fallback**: If model weights are missing or downloading, AgriLens seamlessly defaults to the deterministic engine without throwing errors.

---

## 2. Production Deployment Options

### Option A: Standard Docker Deployment (Recommended)

1. **Clone repository onto the server**:
   ```bash
   git clone <repo-url> /opt/agrilens
   cd /opt/agrilens
   ```

2. **Verify `.env.pro` Configuration**:
   Ensure `.env.pro` is in place with your production settings:
   ```bash
   cp .env.pro .env
   ```

3. **Build and Launch via Docker Compose**:
   ```bash
   docker compose build
   docker compose up -d
   ```

---

### Option B: Pre-Copying Weights (Fast Startup / Zero Bandwidth on Server)

If you already have `qwen2.5-3b-instruct-q4_k_m.gguf` (2.1 GB) on your local machine, transfer it directly to the server to avoid downloading:

1. **SCP the model file to the server**:
   ```bash
   scp "C:\Users\ndoli\Documents\WEBAPP\IHKIP\models\qwen2.5-3b-instruct-q4_k_m.gguf" user@62.171.182.99:/opt/agrilens/data/models/
   ```

2. **Launch Container with Host Volume Mount**:
   ```bash
   docker run -d \
     --name agrilens-web \
     --restart unless-stopped \
     -p 8000:8000 \
     --env-file .env.pro \
     -v /opt/agrilens/data/models:/app/data/models \
     -v /opt/agrilens/media:/app/media \
     ndoli/agrilens:latest
   ```

---

### Option C: Bare Metal / Virtualenv Deployment (Without Docker)

1. **Install Linux System Libraries**:
   ```bash
   sudo apt-get update && sudo apt-get install -y \
       curl \
       libpq-dev \
       libgomp1 \
       build-essential \
       python3-pip \
       python3-venv
   ```

2. **Setup Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements-prod.txt
   ```

3. **Verify Qwen Model Weights**:
   ```bash
   python scripts/download_qwen_model.py
   ```

4. **Run Migrations & Static Collection**:
   ```bash
   export ENV_FILE=.env.pro
   python manage.py migrate --noinput
   python manage.py collectstatic --noinput
   ```

5. **Start Gunicorn Server**:
   ```bash
   gunicorn config.wsgi:application \
       --bind 0.0.0.0:8000 \
       --workers 3 \
       --threads 2 \
       --worker-class gthread \
       --timeout 120 \
       --access-logfile - \
       --error-logfile -
   ```

---

## 3. Server Verification Checklist

Run these quick checks on your production server to confirm 100% operational readiness:

### 1. Healthcheck Endpoint
```bash
curl -I http://localhost:8000/health/
# Expected: HTTP/1.1 200 OK
```

### 2. Public Page Chatbot Presence
```bash
curl -s http://localhost:8000/ | grep -i "publicAiWidgetTrigger"
# Expected: Match found (HTML trigger button present)
```

### 3. Live Qwen Query Test (Public Role)
```bash
curl -X POST http://localhost:8000/api/v1/assistant/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, what is the best planting calendar for maize in Rwanda?"}'
```

### 4. Empirical Statistical Query Test (Database Grounding + Qwen)
```bash
curl -X POST http://localhost:8000/api/v1/assistant/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the average Irish Potato yield in Musanze?"}'
```

---

## 4. Environment Variables Reference (`.env.pro`)

| Variable | Recommended Production Value | Description |
|---|---|---|
| `DEBUG` | `False` | Disables debug mode and activates security headers |
| `ALLOWED_HOSTS` | `agrilens.ndoli.dev,62.171.182.99,localhost` | Trusted HTTP host headers |
| `DATABASE_URL` | `postgres://user:pass@host:5432/agrilens` | Production PostgreSQL connection string |
| `QWEN_LLM_ENABLED` | `True` | Activates local Qwen 2.5 3B neural inference |
| `QWEN_MODEL_PATH` | `/app/data/models/qwen2.5-3b-instruct-q4_k_m.gguf` | Path to quantized GGUF weights |
| `QWEN_MODEL_N_CTX` | `2048` | Context window size (optimal for RAM efficiency) |
| `QWEN_MODEL_TEMPERATURE`| `0.3` | Low temperature ensures disciplined, factual output |
| `QWEN_MODEL_MAX_TOKENS` | `350` | Maximum token limit per response |
| `DOWNLOAD_QWEN_MODEL` | `1` | Automatically checks and downloads weights on startup |
