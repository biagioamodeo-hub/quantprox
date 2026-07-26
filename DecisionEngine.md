# Decision Engine

QuantProX 0.6.0 introduces a deterministic moving-average decision engine.

The engine reads the most recent candles for an instrument and timeframe,
compares configurable short and long simple moving averages, and emits:

- `buy` when the short average is above the long average;
- `sell` when the short average is below the long average;
- `hold` when the averages are equal or history is insufficient.

Each evaluation is stored with its inputs, calculated averages, action,
rationale, and timestamp. Decisions do not submit orders automatically. This
separation keeps strategy evaluation, risk control, and execution independently
auditable.
