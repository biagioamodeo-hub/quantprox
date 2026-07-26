# QuantProX

QuantProX is a quantitative trading framework with a FastAPI service foundation.

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

## Docker

```bash
docker compose up --build
```

This starts the API, PostgreSQL, and pgAdmin (`http://localhost:5050`).

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

## Decision API

Release 0.6.0 adds an auditable moving-average decision engine. Evaluations
produce `buy`, `sell`, or `hold` signals without submitting orders:

- `POST` `/api/v1/decisions/evaluate`
- `GET` `/api/v1/decisions?portfolio_id={portfolio_id}`
