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
- 1.0.0-beta.3: persistent background jobs and asynchronous decisions.
- 1.0.0-beta.4: provider contracts and persistent sandbox broker submissions.
- 1.0.0-beta.5: operational metrics, readiness, rate limiting, and HTTP hardening.
- 1.0.0-rc.1: non-persistent trading recommendations and release-candidate
  consolidation for paper trading.
- 1.0.0: stable, authenticated, localized paper-trading workflow with selectable
  currencies and reference exchange rates.
- 1.1.0: automated prudential assistant, guided investment comparison,
  portfolio-aware signals, and cost-aware demonstrative
  backtesting for inexperienced users.

## Post-1.0 roadmap

- fees and slippage;
- distributed rate limiting, tracing, and production security review.

## Before production trading

- reproducible backtesting and strategy versioning;
- portfolio reconciliation and corporate actions;
- operational runbooks, backup/restore drills, and load testing;
- public API compatibility policy and long-term migration guarantees.
