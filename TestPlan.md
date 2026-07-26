# Test Plan

Every pull request runs on Python 3.11 and 3.12 and must pass:

- Ruff linting;
- Black and isort formatting checks;
- strict mypy type checking;
- pytest with branch coverage.

The alpha test suite covers health, market data, portfolios, risk limits,
orders, decisions, domain errors, paper execution, and the complete
decision-to-execution workflow.

Before publishing a release:

1. install the package with development dependencies;
2. run all quality checks;
3. migrate an empty database from base to head;
4. migrate the database back from head to base;
5. build wheel and source distributions;
6. install the wheel in an isolated environment;
7. verify the health endpoint and package version;
8. require green GitHub Actions checks before merging.
