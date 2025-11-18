# vetc-tool-function — Lightweight data connector tools

vetc-tool-function is a small Python framework of focused helper functions that provide safe, testable access to external data systems commonly used in analytics and automation (Google Sheets, ClickHouse, PostgreSQL). The package exposes thin, well-documented tool functions that return pandas DataFrames or simple Python primitives so they integrate easily into automation pipelines, agents, and ETL jobs.

This README is intended to be used as the package long description (for example, via `long_description` in `setup.py`). It contains an overview, installation steps, quick examples, configuration, development notes, and deployment guidance.

Highlights

- Minimal, opinionated surface: each public function implements one focused capability.
- Connector abstraction: low-level I/O is implemented in `utils/connector/<backend>/providers.py` and `module.py`, making it easy to mock and test.
- Agent-friendly outputs: functions return `pandas.DataFrame` or plain dicts suitable for downstream automation and LLM-driven workflows.

Installation

Install from PyPI (if published) or directly from Git:

```bash
# From PyPI (when published)
pip install vetc-tool-function

# From GitHub
pip install git+https://github.com/yourorg/yourrepo.git@v1.2.0

# From GitLab
pip install git+https://gitlab.com/yourgroup/yourrepo.git@v1.2.0
```

Quickstart

1. Prepare a Python environment and install the package:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .  # or pip install vetc-tool-function
```

2. Configure credentials via environment variables (see "Configuration" below).

3. Import and call a tool function:

```python
from tools.google_sheet.google_sheet_tools import query_google_sheet_data

spreadsheet_id = "YOUR_SPREADSHEET_ID"
df = query_google_sheet_data(spreadsheet_id, range_name="Sheet1!A1:D100")
print(df.head())
```

Available tool modules (examples)

- `tools/google_sheet/google_sheet_tools.py` — read Google Sheet ranges, list tabs, and get document title.
- `tools/clickhouse/clickhouse_tools.py` — execute ClickHouse SQL and query metadata mappings.
- `tools/postgres/postgres_tools.py` — execute Postgres SQL and retrieve Airflow/Superset metadata.

Design and conventions

- Public API: functions under `tools/` are the intended entry points. They validate inputs, call providers and return `pandas.DataFrame` or plain Python types.
- Connectors: `utils/connector/<backend>/providers.py` implements auth and I/O. `module.py` contains client logic when SDK usage is required.
- Configuration: `variables/` contains configuration classes that list expected environment variables. Use `variables.helper.ConfigLoader` in code to load configurations.
- Errors: tool functions catch low-level exceptions, log context, and raise `RuntimeError` with an explanatory message.

Configuration (environment variables)

Common environment variables used by the package:

- Google Sheets
  - `GOOGLE_SHEET_SERVICE_ACCOUNT` — service account JSON as a string (preferred for container environments)
  - `GOOGLE_SHEET_SERVICE_ACCOUNT_JSON_PATH` — path to service account JSON file (useful in local or mounted volumes)

- ClickHouse
  - `CLICKHOUSE_HOST`
  - `CLICKHOUSE_PORT`
  - `CLICKHOUSE_USER`
  - `CLICKHOUSE_PASSWORD`

- Postgres
  - `POSTGRES_HOST`
  - `POSTGRES_PORT`
  - `POSTGRES_USER`
  - `POSTGRES_PASS`
  - `POSTGRES_DB_NAME`

Development

- Install dev dependencies and run tests locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
pytest -q
```

- Tests should mock external I/O. See `tests/` examples for the recommended pattern using `unittest.mock` to patch provider calls.

Documentation and contribution

- High-level documentation files are under `documents/`:
  - `ARCHITECTURE.md` — architecture and data flow.
  - `USAGE.md` — examples and usage guidance.
  - `CONTRIBUTING_NEW_TOOL.md` — how to add a new tool and testing guidelines.
  - `DEPLOYMENT.md` — packaging and publication guidance.

- To add a new tool:
  1. Implement provider functions under `utils/connector/<backend>/providers.py`.
  2. Add a helper client in `utils/connector/<backend>/module.py` if needed.
  3. Add the public function to `tools/<backend>/<backend>_tools.py`.
  4. Add unit tests and documentation.

Packaging and deployment

This project is designed to be packaged as a Python framework. Packaging steps are documented in `documents/DEPLOYMENT.md` and generally include:

1. Update `setup.py` metadata (name, version, description, install_requires, etc.).
2. Build with `python -m build` to create `dist/*.whl` and `dist/*.tar.gz`.
3. Test install locally or from Git tag.
4. Publish to PyPI or a private registry via `twine` or automated CI jobs.

Example CI snippet for publishing (triggered on tags):

```yaml
release:
  image: python:3.10-slim
  script:
    - python -m pip install --upgrade build twine
    - python -m build
    - python -m twine upload -u __token__ -p "$PYPI_TOKEN" dist/*
  only:
    - tags
```

Troubleshooting

- Google Sheets auth errors: verify `GOOGLE_SHEET_SERVICE_ACCOUNT` or `GOOGLE_SHEET_SERVICE_ACCOUNT_JSON_PATH`. Ensure the service account has `spreadsheets.readonly` access to the spreadsheet.
- Database connectivity: confirm host/port/credentials and network rules (VPC, VPN, firewall).
- Empty DataFrame results: validate SQL or sheet range parameters and confirm source data exists.

Security

- Never commit secrets (service account JSON, database passwords, tokens) to source control.
- Use environment variables, CI secret variables, or a secret manager for credentials.
- Use least-privilege service accounts and rotate credentials regularly.

License

Include an appropriate license file at the project root (for example, `LICENSE` containing an Apache-2.0 or MIT license). Update `setup.py` classifiers accordingly.

Contact and support

For questions or contributions, open an issue or a merge request on the repository hosting service (GitHub/GitLab). Include a short description of the change and a reproduction or test case if relevant.

Acknowledgements

This project follows small, testable design patterns inspired by common data engineering practices: thin connectors, explicit configuration, and reproducible packaging.

