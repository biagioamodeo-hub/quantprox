# Changelog

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
