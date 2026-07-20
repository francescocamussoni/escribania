# Research: Extensiones de Plataforma — Cotizaciones, Configuración y Libros Contables

**Feature**: `002-platform-extensions`  
**Date**: 2026-07-18  
**Status**: Complete — all NEEDS CLARIFICATION resolved

---

## Argentine Dollar Exchange Rate APIs

### Decision
Use **ArgentinaDatos** (`api.argentinadatos.com`) as the primary source for all
date-based historical queries. Use **DolarAPI** (`dolarapi.com`) as a fallback for
the current-day rate only (today's date), since DolarAPI does not support historical lookups.

### Rationale
ArgentinaDatos is the only publicly available free API that natively supports date-based
historical queries via path parameters with no authentication. It covers both `bolsa`
(Dólar MEP) and `oficial` (Banco Nación) casas — the exact two exchange rates the
platform requires. No rate limiting is documented; response time ~159ms. CORS is enabled,
which is irrelevant since the spec mandates backend-only calls.

DolarAPI is more stable for real-time (today's) rate but provides no historical endpoint.
It serves as a complement for the edge case where ArgentinaDatos returns no data for today.

### Alternatives considered
- **DolarAPI only**: Cannot serve historical dates — rules it out as primary.
- **bluelytics.com.ar**: No MEP/bolsa support, no historical endpoint, unstable docs.
- **BCRA Series API (`apis.datos.gob.ar`)**: Official BNA source, but no MEP (bond market rate,
  not published by BCRA), complex query interface.

### Endpoint patterns

```
# ArgentinaDatos — historical by date (PRIMARY for all dates)
GET https://api.argentinadatos.com/v1/cotizaciones/dolares/{casa}/{fecha}
  casa:  "bolsa"   → Dólar MEP
  casa:  "oficial" → Dólar Banco Nación
  fecha: YYYY/MM/DD  (e.g. 2025/03/15)
  Response: { "moneda": "USD", "casa": "bolsa", "fecha": "2025-03-15",
              "compra": 1190.5, "venta": 1195.0 }

# DolarAPI — current rate only (FALLBACK for today's date)
GET https://dolarapi.com/v1/dolares/bolsa
GET https://dolarapi.com/v1/dolares/oficial
  Response: { "compra": 0, "venta": 0, "casa": "bolsa",
              "fechaActualizacion": "2026-07-18T..." }
```

Both APIs: HTTPS, CORS enabled, no auth, free, JSON. The backend MUST proxy all calls;
the frontend MUST NOT call these APIs directly (FR-006).

The configured `COTIZACION_API_URL` env var maps to the ArgentinaDatos base URL.
A `COTIZACION_FALLBACK_URL` env var maps to the DolarAPI base URL.

---

## Backend Cache Strategy (8-hour TTL, keyed by date)

### Decision
**`cachetools.TTLCache`** — in-process module-level singleton, keyed by `(casa, date_iso)`,
TTL = 28,800 seconds (8 hours). For past dates (strictly before today), use an unbounded
`dict` (historical rates never change after market close).

### Rationale
Single ECS Fargate task, < 10 concurrent users, no Redis provisioned. `cachetools` is
zero-infra, thread-safe within a single asyncio event loop (single uvicorn worker), and
trivially testable by replacing the cache in tests. Adding Redis would introduce standing
cost (~$15/month for ElastiCache) and ops overhead that exceeds the benefit for this
volume.

Historical rates (past dates) are immutable after market close — they can be cached
permanently (no TTL). Only today's rate needs an 8h TTL since it may be updated
intra-day by the source.

### Alternatives considered
- **Redis**: Correct for multi-worker/multi-instance. Not provisioned; adds cost and ops.
- **PostgreSQL cache table**: Durable across restarts, audit-friendly. Adds a DB round-trip
  on every rate lookup. Could be combined with cachetools for warm-cache-from-DB pattern
  on restart — deferred to implementation if needed.
- **`functools.lru_cache`**: No TTL support; unsuitable.

### Implementation pattern

```python
from cachetools import TTLCache
from datetime import date
import httpx

# Today's rate: TTL 8h (28800s); past dates: permanent dict
_today_cache: TTLCache = TTLCache(maxsize=10, ttl=28_800)
_history_cache: dict = {}

async def get_exchange_rate(casa: str, fecha: date) -> dict:
    is_today = fecha >= date.today()
    cache = _today_cache if is_today else _history_cache
    cache_key = (casa, fecha.isoformat())

    if cache_key in cache:
        return cache[cache_key]

    fecha_path = fecha.strftime("%Y/%m/%d")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{settings.COTIZACION_API_URL}/v1/cotizaciones/dolares/{casa}/{fecha_path}"
        )
        resp.raise_for_status()  # propagate as CotizacionAPIError

    data = resp.json()
    cache[cache_key] = data
    return data
```

Error handling: any non-200 response or network timeout raises a domain exception
(`CotizacionAPIError`) that the endpoint translates to a user-facing error message
(FR-003). The cache is NOT populated on error.

---

## Soft Delete Pattern — SQLAlchemy 2.0 Async + PostgreSQL

### Decision
`SoftDeleteMixin` with `deleted_at: Mapped[datetime | None]` + `do_orm_execute` event
listener with `with_loader_criteria()` for global filtering. PostgreSQL **partial unique
index** (`WHERE deleted_at IS NULL`) for the `Escribano.nombre` uniqueness constraint.

This same pattern applies to `Empleado` (soft delete for employees).

### Rationale
`do_orm_execute` + `with_loader_criteria` is the official SQLAlchemy 2.0 documented
pattern for transparent row-level filtering in async sessions. It propagates to
relationship loaders automatically, does not require custom Query subclasses (the 1.x
pattern, incompatible with 2.0 async `select()`), and supports an escape hatch via
`execution_options(include_deleted=True)` for admin/audit queries.

The partial unique index is race-condition-free: it enforces uniqueness only among rows
where `deleted_at IS NULL`, allowing a deleted name to be reused without application-layer
TOCTOU checks.

### Pitfall — FK visibility
When `Escribano` is soft-deleted, `Escritura.escribano_id` FK still points to the
physically present row. However, `with_loader_criteria` makes the `Escribano` invisible
in regular relationship loads (`is_relationship_load=True` check). **Mitigation**: snapshot
the `escribano_nombre` as a VARCHAR column on `Escritura` at creation time — this ensures
the UI can always display the name even if the escribano is later soft-deleted, without
requiring `include_deleted=True` on every escritura query.

### Alternatives considered
- **`is_active: bool` flag**: No audit trail (when deleted?). Rejected.
- **Archive table**: Clean semantics, complex migration, overkill at this domain size.
- **Application-layer uniqueness check**: TOCTOU race condition. Forbidden.

### Key patterns

```python
# models/mixins.py
class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    def soft_delete(self) -> None:
        self.deleted_at = datetime.utcnow()

# Partial unique index on Escribano
class Escribano(Base, SoftDeleteMixin):
    __table_args__ = (
        Index("uq_escribano_nombre_active", "nombre", unique=True,
              postgresql_where=text("deleted_at IS NULL")),
    )
    nombre: Mapped[str] = mapped_column(nullable=False)
    # Escritura snapshots nombre at creation → not impacted by later soft-delete

# Global filter event (registered once in database.py)
@event.listens_for(Session, "do_orm_execute")
def _apply_soft_delete_filter(execute_state):
    if (execute_state.is_select
            and not execute_state.is_column_load
            and not execute_state.is_relationship_load
            and not execute_state.execution_options.get("include_deleted", False)):
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                SoftDeleteMixin,
                lambda cls: cls.deleted_at.is_(None),
                include_aliases=True,
            )
        )
```

---

## New Dependencies

| Package | Version | Purpose |
|---|---|---|
| `cachetools` | latest | In-process TTL cache for exchange rate API |
| `httpx` | latest (already likely present) | Async HTTP client for external API calls |

Both packages are well-established, zero-infra additions. `httpx` may already be a
transitive dependency via FastAPI; adding it explicitly pins the version.

---

## Summary: Decisions Made

| Topic | Decision |
|---|---|
| Exchange rate API (primary) | ArgentinaDatos `api.argentinadatos.com` — historical by date |
| Exchange rate API (fallback) | DolarAPI `dolarapi.com` — current day only |
| Cache layer | `cachetools.TTLCache` in-process; 8h TTL for today; permanent for past dates |
| Soft delete | `deleted_at` mixin + `do_orm_execute` filter + partial unique index on `nombre` |
| FK name snapshot | `Escritura` stores `escribano_nombre` VARCHAR at creation for display resilience |
