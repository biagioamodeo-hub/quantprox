# QuantProX

QuantProX is a quantitative trading framework with a FastAPI service foundation.

The current release is **1.0.0-beta.5**. It is intended for local development
and paper-trading workflows; it must not be connected to live brokerage
execution.

## Requirements

- Python 3.11 or newer
- PostgreSQL 16 (or Docker)

## Local development

```bash
cp .env.example .env
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`; interactive documentation is at
`http://localhost:8000/docs`.

The guided Alpha Lab interface is available at `http://localhost:8000/lab/`.

## Authentication and tenant isolation

Every `/api/v1` request requires an `X-API-Key` header. Configure tenant keys
through `TENANT_API_KEYS`, a JSON object mapping stable tenant identifiers to
secrets:

```bash
TENANT_API_KEYS={"demo":"replace-with-a-long-random-secret"}
```

Portfolios and every portfolio-derived risk check, decision, order, position,
valuation, and execution are isolated by tenant. Unknown keys receive `401`;
resources owned by another tenant are returned as `404` to avoid leaking their
existence. Market-data resources are shared across tenants but still require
authentication.

Alpha Lab includes a password-style field for the tenant key and sends it only
as the `X-API-Key` request header.

## Idempotent mutations

Order creation, decision-to-order creation, and paper execution accept an
optional `Idempotency-Key` header of up to 128 characters. Retrying the same
operation with the same key and payload returns the original resource without
duplicating an order, fill, cash movement, or position update. Reusing a key
with a different payload returns `409 Conflict`.

Keys are scoped to a portfolio for orders and to an order for executions.
Clients should generate a new opaque key for each logical operation and retain
it until that operation has completed.

## Background jobs

Decision evaluation can run asynchronously:

- `POST /api/v1/jobs/decisions/evaluate` returns a queued job with HTTP 202.
- `GET /api/v1/jobs/{job_id}` reports tenant-isolated state and result.

Jobs are persisted in PostgreSQL and claimed by the worker using row locks with
`SKIP LOCKED`, allowing multiple workers without duplicate claims. Failed jobs
are retried up to their configured limit. Decision jobs are linked uniquely to
their result, so a worker restart after evaluation cannot create a duplicate
decision. Job submission also supports `Idempotency-Key`.

## Broker sandbox

Provider-neutral protocols define the broker order and market-data boundaries.
The first broker implementation is a deterministic local sandbox:

- `POST /api/v1/brokers/sandbox/orders/{order_id}` submits an accepted order.
- `GET /api/v1/brokers/sandbox/orders/{order_id}` returns external state.
- `POST /api/v1/brokers/sandbox/orders/{order_id}/cancel` cancels both the
  sandbox submission and the corresponding local open order.

Submission is replay-safe: an order has at most one external submission.
Rejected, filled, partially filled, or cancelled orders cannot be submitted.
The sandbox adapter is explicitly marked non-live and performs no network or
brokerage operation.

## Operations and security

- `GET /health` reports process liveness.
- `GET /ready` verifies that PostgreSQL is reachable.
- `GET /api/v1/metrics` exposes authenticated Prometheus text metrics.

Every response includes a validated or generated `X-Request-ID`, defensive
browser headers, and a structured JSON access-log entry. Alpha Lab also receives
a restrictive Content Security Policy.

Versioned API requests are rate limited by API key (or client address when no
key is supplied). Configure the fixed window with `RATE_LIMIT_ENABLED`,
`RATE_LIMIT_REQUESTS`, and `RATE_LIMIT_WINDOW_SECONDS`. Responses include
`X-RateLimit-Limit` and `X-RateLimit-Remaining`; exhausted clients receive
`429 Too Many Requests` and `Retry-After`.

The limiter and metrics registry are intentionally in-memory for this beta.
Deployments with multiple API processes need a shared limiter and metrics
aggregation before production use.

## Docker

```bash
docker compose up --build
```

This runs migrations and starts the API, PostgreSQL, a persistent background
worker, and pgAdmin (`http://localhost:5050`). Docker also checks API liveness.

## Database migrations

```bash
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

## Quality checks

```bash
ruff check .
black --check .
isort --check-only .
mypy app
pytest --cov=app
```

## Project layout

`app/` contains API routes, configuration, database integration, domain models,
schemas, services, repositories, dependencies, and utilities. `tests/` contains
the automated test suite. GitHub Actions runs formatting, linting, type checks,
and tests for each pull request.

## Roadmap

Release 0.1.0 establishes the backend foundation. Trading, portfolio, risk, and
decision-engine features follow in later releases.

## Market data API

Release 0.2.0 introduces provider-neutral storage for instruments and OHLCV
candles. The endpoints are available under `/api/v1/market-data`:

- `POST` and `GET` `/instruments`
- `POST` and `GET` `/candles`

## Portfolio API

Release 0.3.0 adds portfolio and position tracking. The endpoints are available
under `/api/v1/portfolios`:

- `POST` and `GET` `/`
- `POST` `/positions`
- `GET` `/{portfolio_id}/positions`
- `GET` `/{portfolio_id}/valuation?timeframe=1d`

Portfolio valuations use the latest close for the selected timeframe and report
market value, gross exposure, equity, and realized and unrealized P&L. Positions
without a matching candle explicitly report `cost_basis` as their price source.

## Risk API

Release 0.4.0 introduces portfolio risk limits and deterministic pre-trade
checks based on current cost-basis exposure:

- `PUT` and `GET` `/api/v1/risk/limits/{portfolio_id}`
- `POST` `/api/v1/risk/checks/orders`

## Orders API

Release 0.5.0 adds risk-gated limit-order submission and an audit trail for both
accepted and rejected orders:

- `POST` `/api/v1/orders`
- `GET` `/api/v1/orders?portfolio_id={portfolio_id}`
- `POST` `/api/v1/orders/{order_id}/cancel`

Accepted orders may be cancelled before execution. Cancellation is timestamped
and terminal; rejected, filled, and already-cancelled orders cannot be cancelled.

## Decision API

Release 0.6.0 adds an auditable moving-average decision engine. Evaluations
produce `buy`, `sell`, or `hold` signals without submitting orders:

- `POST` `/api/v1/decisions/recommend` returns a non-persistent trading
  recommendation with its moving averages, rationale, and disclaimer.
- `POST` `/api/v1/decisions/evaluate`
- `GET` `/api/v1/decisions?portfolio_id={portfolio_id}`
- `POST` `/api/v1/decisions/{decision_id}/orders`

Recommendations are quantitative signals for informational purposes only. They
do not create orders and are not financial advice.

## Paper execution API

The alpha release completes the auditable paper-trading path. Accepted orders
can be filled at their limit price, updating portfolio cash and positions in one
database transaction:

- `POST` `/api/v1/executions/orders/{order_id}`
- `GET` `/api/v1/executions?portfolio_id={portfolio_id}`

The execution request may include `{"quantity": "..."}` for a partial fill.
Omitting the body fills the entire remaining quantity. Each fill is recorded
separately, while the order exposes filled and remaining quantities.

Rejected orders, hold decisions, insufficient cash, insufficient position
quantity, and repeated execution attempts are never executed.

## Alpha workflow

1. Create an instrument and load OHLCV candles.
2. Create a portfolio with a paper cash balance.
3. Configure portfolio risk limits.
4. Evaluate a decision.
5. Create an order from a `buy` or `sell` decision.
6. Execute an accepted order through the paper execution endpoint.
7. Inspect orders, executions, positions, and cash balance.
