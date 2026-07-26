# Changelog

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
