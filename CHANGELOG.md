# Changelog

## 1.0.0-rc.1

- Add a non-persistent endpoint for `buy`, `sell`, and `hold` recommendations.
- Return the moving-average inputs, rationale, and an informational disclaimer.
- Reuse the recommendation calculation for auditable decision evaluations.
- Promote the tested paper-trading feature set to its first release candidate.
- Retain the explicit prohibition on live brokerage execution.

## 1.0.0-beta.5

- Add request IDs, structured access logs, and defensive HTTP headers.
- Add authenticated Prometheus text metrics and database readiness checks.
- Add configurable fixed-window rate limiting for versioned API requests.
- Add API container health monitoring and operational documentation.

## 1.0.0-beta.4

- Add provider-neutral broker and market-data adapter contracts.
- Add a deterministic, non-live broker sandbox.
- Persist replay-safe external submissions and tenant-isolated status.
- Synchronize sandbox cancellation with the local open order.

## 1.0.0-beta.3

- Add persistent, tenant-isolated background jobs.
- Add asynchronous decision evaluation with queryable results.
- Add a Docker worker, automatic migrations, safe concurrent claims, and retries.
- Make decision job results restart-safe and job submission idempotent.

## 1.0.0-beta.2

- Add optional `Idempotency-Key` support to order and execution mutations.
- Replay successful resources without duplicate financial side effects.
- Reject reuse of an idempotency key with a different request payload.

## 1.0.0-beta.1

- Require configurable API keys for all versioned API endpoints.
- Isolate portfolios and portfolio-derived resources by tenant.
- Return uniform authorization failures without leaking cross-tenant resources.
- Add tenant-key support to Alpha Lab and migration existing data to `demo`.

## 1.0.0-alpha.5

- Restore pgAdmin startup compatibility with its email validation.
- Verify the complete Docker Compose stack and alpha web endpoints.

## 1.0.0-alpha.4

- Allow multiple partial fills for an open order.
- Track filled and remaining order quantities.
- Keep partially filled orders cancellable and reject overfills.

## 1.0.0-alpha.3

- Add timestamped cancellation for accepted orders.
- Prevent cancelled orders from being executed or cancelled repeatedly.
- Expose cancellation as an optional branch in Alpha Lab.

## 1.0.0-alpha.2

- Add portfolio mark-to-market valuation using the latest timeframe close.
- Track realized P&L on sell executions and report unrealized P&L.
- Make projected exposure sensitive to order side and instrument.

## 1.0.0-alpha.1

- Complete the auditable market-data-to-paper-execution workflow.
- Add one-time paper fills that update cash and positions transactionally.
- Allow `buy` and `sell` decisions to create risk-gated orders explicitly.
- Add consistent domain and database-conflict API responses.
- Document alpha scope, architecture, risk assumptions, and verification.

## 0.6.0

- Add an SMA-based `buy`, `sell`, and `hold` decision engine.
- Persist decision inputs, calculated averages, actions, and rationales.
- Add decision query endpoints, migration, and API tests.

## 0.5.0

- Add risk-gated limit-order submission.
- Persist accepted and rejected orders with rejection reasons.
- Add order query endpoints, migration, and API tests.

## 0.4.0

- Add per-portfolio order-notional and total-exposure limits.
- Add deterministic pre-trade order checks.
- Add the risk-limit database migration and API tests.

## 0.3.0

- Add portfolio and position persistence.
- Add REST endpoints for creating and listing portfolios and positions.
- Add the second Alembic migration for portfolio tables.

## 0.2.0

- Add provider-neutral instruments and OHLCV candle storage.

## 0.1.0

- Establish the FastAPI, settings, SQLAlchemy, Alembic, Docker, and CI foundation.
