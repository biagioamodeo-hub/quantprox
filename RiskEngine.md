# Risk Engine

The alpha risk engine applies two limits per portfolio:

- maximum notional for one order;
- maximum projected gross exposure.

Current exposure uses position quantity multiplied by the latest available
market close, falling back to average entry price when market data is missing.
Projected exposure replaces the target instrument's current exposure with its
post-order quantity at the order price. Reducing sells therefore reduce gross
exposure, while sells beyond the current long quantity create short exposure.

An order is rejected when limits are missing or either configured threshold is
exceeded. Rejected orders remain persisted with a human-readable reason.

Risk checks are deterministic controls, not financial advice or a guarantee
against loss.
