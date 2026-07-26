# Roadmap

## Completed

- 0.1.0: FastAPI, settings, database, migrations, Docker, and CI foundation.
- 0.2.0: instruments and OHLCV market data.
- 0.3.0: portfolios and positions.
- 0.4.0: portfolio risk limits and pre-trade checks.
- 0.5.0: persistent, risk-gated orders.
- 0.6.0: auditable moving-average decisions.
- 1.0.0-alpha.1: end-to-end paper execution and alpha hardening.
- 1.0.0-alpha.2: mark-to-market valuation, P&L, and side-aware exposure.
- 1.0.0-alpha.3: auditable cancellation of accepted orders.
- 1.0.0-alpha.4: multiple partial fills with remaining-quantity tracking.
- 1.0.0-alpha.5: Docker Compose and pgAdmin startup hardening.
- 1.0.0-beta.1: API-key authentication and tenant-isolated portfolios.
- 1.0.0-beta.2: idempotent order and paper-execution mutations.

## Beta roadmap

- fees and slippage;
- background jobs;
- broker/provider adapter interfaces and sandbox integration;
- production observability, rate limiting, and security review.

## Before stable

- reproducible backtesting and strategy versioning;
- portfolio reconciliation and corporate actions;
- operational runbooks, backup/restore drills, and load testing;
- public API compatibility policy and long-term migration guarantees.
