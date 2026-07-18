# Research: Plataforma Contable — Escribanía

**Feature**: `001-plataforma-contaduria`  
**Date**: 2026-07-18  
**Status**: Complete — all NEEDS CLARIFICATION resolved

---

## Tech Stack Decisions

### Real-time push: SSE vs WebSockets

- **Decision**: Server-Sent Events (SSE)
- **Rationale**: Only server→client push is needed when an escritura changes. SSE is plain
  HTTP (`StreamingResponse` + `text/event-stream`), works with standard auth cookies, and
  browsers reconnect automatically via `EventSource`. For <10 users, pair with PostgreSQL
  `LISTEN/NOTIFY` or in-process pub/sub on a single Fargate task — no Redis required.
- **Alternatives considered**: WebSockets (overkill — no bidirectional traffic needed);
  polling (forbidden by constitution P5)

---

### ORM: SQLAlchemy 2.0 async + Alembic

- **Decision**: SQLAlchemy 2.0 (async) with `asyncpg` driver + Alembic for migrations;
  Pydantic v2 response schemas kept separate from ORM models.
- **Rationale**: Most battle-tested FastAPI/PostgreSQL stack in 2025–2026. Rich async query
  tooling, mature Alembic migrations (auto-diff, branching, rollbacks). Keeping ORM models
  and DTOs separate enforces the constitution P7 rule (no raw ORM serialization to clients).
- **Alternatives considered**: SQLModel (thin wrapper, less flexible as schemas diverge);
  Tortoise + Aerich (nicer DX, weaker migration ecosystem)

---

### Authentication: JWT in HttpOnly cookies

- **Decision**: JWT access tokens stored in `HttpOnly` + `Secure` + `SameSite=Strict`
  cookies; 8-hour absolute expiry; logout clears cookie.
- **Rationale**: For <10 internal users and a single API instance, JWT avoids Redis/
  ElastiCache cost and ops. Cookie storage (vs localStorage) avoids XSS token theft.
  A small Postgres-backed denylist can be added later if instant revoke is needed.
- **Alternatives considered**: Redis-backed opaque sessions (better instant revoke; adds
  standing cost); Postgres-backed sessions (good middle ground if revoke needed)

---

### Frontend: React + Vite (SPA)

- **Decision**: React + Vite single-page application, deployed as static assets to
  S3 + CloudFront.
- **Rationale**: Auth-gated internal UI with three sections and SSE streams has no
  SEO/SSR requirement. Vite keeps the mental model simple (SPA → FastAPI). Static
  assets on S3+CloudFront are near-zero cost. Avoids Next.js server-runtime complexity
  on ECS.
- **Alternatives considered**: Next.js (useful for SSR/SEO — not needed here); Vue/Svelte
  (equally fine technically; React chosen for wider ecosystem/hiring)

---

### AWS Deployment: ECS Fargate + RDS PostgreSQL

- **Decision**: ECS Fargate (private subnets, no public IP) + RDS PostgreSQL `db.t4g.micro`
  + internal ALB (or AWS Client VPN for direct staff access). Static frontend on
  S3 + CloudFront.
- **Rationale**: Fargate sits natively in VPC with security groups blocking direct public
  access to the API — the cleanest fit for "no public endpoint" (constitution P7, FR-021).
  Cost target <USD 50/month achieved with 0.25 vCPU / 0.5 GB task, VPC endpoints for
  ECR/Secrets Manager/CloudWatch (avoid NAT gateway charges), and `db.t4g.micro`.
- **Alternatives considered**: App Runner + PrivateLink (simpler deploy UX; harder to stay
  under budget with always-on + VPC connector overhead); EC2 + Docker Compose (cheapest,
  most DIY ops burden)
- **Estimated monthly cost**: ~$15–25 (Fargate task ~$8, RDS micro ~$12, CloudFront/S3 ~$2)

---

## Data Modeling Decisions

### Immutable Financial Records: Mutable Snapshot + Freeze on Close

- **Decision**: Persist all calculated amounts as columns on `FacturaPrincipal` (mutable
  snapshot while open; frozen when Escritura is closed). No derive-on-read for closed
  records.
- **Rationale**: Open documents need full recalculation when FX rates or inputs change.
  Closed documents must never change even if formulas or rates evolve. Storing amounts gives
  fast liquidación reads and historical fidelity. App-layer rules (+ optional DB trigger)
  enforce immutability when `estado = cerrada`.
- **Alternatives considered**: Pure derive-on-read (fragile for closed history); append-only
  event store (overkill at this volume); dual tables draft/posted (cleaner semantics, more schema)

---

### Monthly Scoping: `created_at` + Range Index

- **Decision**: Single table with `created_at TIMESTAMPTZ` + B-tree index. Query months
  with half-open range (`>= month_start AND < next_month_start`). Optional denormalized
  `anio`/`mes` columns for domain clarity — not for performance.
- **Rationale**: At <200 rows/month, index range scan is trivial; partitioning adds
  planner/ops overhead with no measurable gain. Avoid `EXTRACT(month/year)` in WHERE
  clauses (breaks index use).
- **Alternatives considered**: Explicit `year`+`month` columns (redundant if derived
  consistently from `created_at`); range partitioning (useful at high volume/retention
  drop scenarios); physical table-per-month (worst maintainability)

---

### Configuration Versioning: Immutable Versioned Rows + FK

- **Decision**: Insert a new `ConfiguracionFinanciera` row for each config change (never
  UPDATE in place). Each `Escritura` stores an FK to the config version used at creation.
  `FacturaPrincipal` persists the calculated amounts (source of truth); config FK enables
  "why these numbers?" audit. Key rates optionally denormalized onto the invoice for
  self-contained audit trail.
- **Rationale**: Ensures old escrituras keep pointing to the exact rates used, even after
  the admin changes current rates. FK preserves referential integrity. Persisted invoice
  amounts remain the financial source of truth for liquidación.
- **Alternatives considered**: Copy all rate fields into every FacturaPrincipal (self-
  contained but duplicates schema); JSON snapshot only (flexible, hard to constrain/query);
  soft effective_from/to on one mutable row (easy to get wrong under concurrent edits)

---

## Summary: Final Stack

| Layer | Technology | Notes |
|---|---|---|
| Backend language | Python 3.12 | per constitution P3 |
| Backend framework | FastAPI (async) | OpenAPI auto-gen, SSE support |
| ORM | SQLAlchemy 2.0 async + asyncpg | |
| Migrations | Alembic | |
| Response schemas | Pydantic v2 (separate from ORM) | |
| Database | PostgreSQL 16 | local: Docker; prod: RDS t4g.micro |
| Real-time | SSE via FastAPI StreamingResponse + PG LISTEN/NOTIFY | |
| Auth | JWT in HttpOnly cookies, 8h expiry | |
| Frontend | React 18 + Vite (SPA) | TypeScript |
| Frontend deploy | S3 + CloudFront | |
| Backend deploy | ECS Fargate private subnet | |
| IaC / local | Docker Compose | mirrors AWS services |
| CI/CD | GitHub Actions (suggested) | |
