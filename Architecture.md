# Architecture

QuantProX alpha is a layered FastAPI application:

1. API routes validate HTTP input and expose versioned endpoints.
2. Services implement market-data, portfolio, risk, decision, order, and paper
   execution use cases.
3. Repositories isolate SQLAlchemy reads and writes.
4. ORM models define the PostgreSQL persistence layer.
5. Alembic migrations evolve the schema in a linear, reversible chain.

The primary workflow is:

`candles → decision → risk-gated order → paper execution → cash/position update`

Decision generation never submits an order implicitly. Order creation never
executes an order implicitly. These explicit boundaries make every transition
auditable and allow later broker integrations to replace paper execution
without changing the strategy layer.

The alpha is a synchronous single-service deployment. Background processing,
live brokerage adapters, authentication, multi-tenancy, and distributed event
delivery are intentionally outside its scope.
