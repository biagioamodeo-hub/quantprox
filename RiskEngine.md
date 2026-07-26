# Risk Engine

The alpha risk engine applies two limits per portfolio:

- maximum notional for one order;
- maximum projected gross exposure.

Current exposure uses position quantity multiplied by average entry price.
Projected exposure conservatively adds the absolute order notional. This means
sell orders are treated as exposure-increasing during pre-trade evaluation.
That conservative simplification is acceptable for the alpha but should be
replaced by side-aware, instrument-aware exposure calculation before beta.

An order is rejected when limits are missing or either configured threshold is
exceeded. Rejected orders remain persisted with a human-readable reason.

Risk checks are deterministic controls, not financial advice or a guarantee
against loss.
