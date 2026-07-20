# Quickstart: Plataforma Contable — Escribanía

**Feature**: `001-plataforma-contaduria`  
**Date**: 2026-07-18

This guide describes how to run and validate the system end-to-end in the two
supported environments: **local** (Docker Compose) and **AWS production**.

---

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Docker | 24+ | Local containers |
| Docker Compose | 2.x | Local orchestration |
| Python | 3.12 | Backend (dev/test only) |
| Node.js | 20 LTS | Frontend (dev only) |
| AWS CLI | 2.x | Production deploy |
| psql | 16+ | DB inspection |

---

## Local Development

### Option A — Makefile (recommended for day-to-day dev)

```bash
git clone <repo-url> escribania
cd escribania

# Start PostgreSQL
make db-up

# First-time setup: migrations + seed config + admin user
make setup

# Terminal 1 — API on :8000
make run

# Terminal 2 — frontend on :5173
make frontend-dev
```

Default credentials after `make setup`: `admin` / `tu-password`

Run the end-to-end smoke test (API must be running):

```bash
SMOKE_PASSWORD=tu-password make smoke
```

### Option B — Docker Compose (full stack in containers)

### 1. Clone and configure environment

```bash
git clone <repo-url> escribania
cd escribania
cp .env.example .env          # fill in secrets (never commit .env)
```

**Minimum `.env` values for local**:
```
POSTGRES_USER=escribania
POSTGRES_PASSWORD=<local-secret>
POSTGRES_DB=escribania_db
JWT_SECRET=<32-char-random-string>
JWT_EXPIRY_HOURS=8
ENVIRONMENT=local
```

### 2. Start all services

```bash
docker compose up --build
```

This starts:
- `db` — PostgreSQL 16 on port 5432
- `backend` — FastAPI on port 8000; on startup runs the same steps as `make setup`
  (migrations, config seed, admin user) plus demo escrituras when `SEED_DEMO_DATA=true`
- `frontend` — Vite dev server on port 5173 (hot-reload)

Default credentials (created automatically): `admin` / `tu-password`

Override via environment variables on the `backend` service if needed:
`ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_DISPLAY_NAME`.

### 3. Access the platform

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API docs | http://localhost:8000/api/v1/docs |
| Backend health | http://localhost:8000/api/v1/health |

### 4. Validate canonical calculation

```bash
docker compose exec backend python -m pytest tests/unit/test_calculo_factura.py -v
```

Expected: all tests pass using the USD 105,000 fixture from `constitution.md`.

---

## Running Tests (TDD)

All tests must be written and confirmed FAILING before implementing the feature.

```bash
# All unit tests (calculation engine)
docker compose exec backend python -m pytest tests/unit/ -v

# Integration tests (API endpoints)
docker compose exec backend python -m pytest tests/integration/ -v

# All tests (from repo root)
make test

# Or inside backend/
cd backend && .venv/bin/pytest -v
```

### Canonical test fixture

The test suite uses the values from `constitution.md` §5 as the primary fixture.
Every calculation test MUST assert exact equality against those values.

---

## Local → AWS Parity Validation

To confirm local and production behave identically:

1. Run the canonical calculation test locally → note all output values
2. Deploy to AWS (see below)
3. Run the same test against the production API using `pytest --env=prod`
4. Assert all values match

The only permitted differences are: database host, JWT secret, log destinations.
No code-path differences are allowed (constitution P1).

---

## AWS Production Deployment

### Infrastructure overview

```
Internet
    │
    ▼
CloudFront (HTTPS) ──► S3 bucket (React SPA static assets)
    │
    ▼
Application Load Balancer (internal, VPC only)
    │
    ▼
ECS Fargate task (FastAPI, private subnet)
    │
    ▼
RDS PostgreSQL db.t4g.micro (private subnet, no public IP)
```

### Deploy backend

```bash
# Build and push Docker image
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <ecr-uri>
docker build -t escribania-backend ./backend
docker tag escribania-backend:latest <ecr-uri>/escribania-backend:latest
docker push <ecr-uri>/escribania-backend:latest

# Update ECS service (triggers rolling deploy)
aws ecs update-service \
  --cluster escribania \
  --service escribania-backend \
  --force-new-deployment
```

### Deploy frontend

```bash
cd frontend
npm run build
aws s3 sync dist/ s3://<bucket-name> --delete
aws cloudfront create-invalidation --distribution-id <dist-id> --paths "/*"
```

### Run migrations on production

```bash
# Run as a one-off ECS task (not in the running service)
aws ecs run-task \
  --cluster escribania \
  --task-definition escribania-migration \
  --overrides '{"containerOverrides":[{"name":"backend","command":["alembic","upgrade","head"]}]}'
```

### Environment variables (injected via AWS Secrets Manager)

| Variable | Description |
|---|---|
| `POSTGRES_DSN` | Full async DSN: `postgresql+asyncpg://user:pass@host/db` |
| `JWT_SECRET` | 32+ char random string |
| `JWT_EXPIRY_HOURS` | `8` |
| `ENVIRONMENT` | `production` |
| `CORS_ORIGINS` | CloudFront distribution URL |

---

## Smoke Test (post-deploy)

```bash
# Health check
curl https://<cloudfront-url>/api/v1/health

# Login
curl -c cookies.txt -X POST https://<cloudfront-url>/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"<password>"}'

# Fetch active config
curl -b cookies.txt https://<cloudfront-url>/api/v1/configuracion
```

Expected: all return HTTP 200 with valid JSON.

---

## Validating Real-Time Updates (SSE)

Open two browser tabs:
1. Tab 1 → Liquidación section for current month
2. Tab 2 → Create a new Escritura

After saving in Tab 2, the liquidación totals in Tab 1 should update within 2 seconds
without any page reload (constitution P5, SC-003).

---

## Common Issues

| Problem | Likely cause | Fix |
|---|---|---|
| `alembic upgrade head` fails | DB not ready | Wait 5s and retry; check `docker compose logs db` |
| JWT cookie not set | HTTP in local | Frontend must call API on `localhost:8000` (same origin handling) |
| SSE disconnects immediately | Reverse proxy timeout | Set `proxy_read_timeout 600s` (nginx) or ALB idle timeout ≥ 60s |
| Calculation mismatch | Stale config version | Re-seed config and re-create the test escritura |
