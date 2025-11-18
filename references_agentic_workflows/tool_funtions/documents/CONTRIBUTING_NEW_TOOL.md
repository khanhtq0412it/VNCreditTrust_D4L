# How to Create a New Tool / Function

This guide explains how to add a new public tool function to the repository and the recommended project conventions for design, testing, and documentation.

Quick checklist

- [ ] Implement a thin provider in `utils/connector/<backend>/providers.py` for I/O and auth.
- [ ] Add a client or helper in `utils/connector/<backend>/module.py` if SDK usage or complex auth is required.
- [ ] Add the public function in `tools/<backend>/<backend>_tools.py`.
- [ ] Add unit tests (happy path + 1-2 edge cases) under `tests/`.
- [ ] Add usage example or update `documents/USAGE.md`.
- [ ] Run linting and tests, open a PR.

Design contract (2–4 bullets)

- Inputs: simple primitives (str, int, list, dict). Keep parameters explicit.
- Outputs: `pandas.DataFrame` for tabular data; `dict`/`str` for metadata/lookups.
- Errors: raise `RuntimeError` with a clear message; log the underlying exception at DEBUG level.
- Side effects: avoid stateful side effects in public functions (perform writes only when explicitly named and documented).

Detailed steps

1. Pick a namespace

- Existing backends: use `tools/<backend>/` and `utils/connector/<backend>/`.
- New backend: create `tools/<new_backend>/` and `utils/connector/<new_backend>/` with the same conventions.

2. Implement the provider (I/O + auth)

- Location: `utils/connector/<backend>/providers.py`.
- Responsibilities:
  - Authenticate to the remote service (or use `module.py` client).
  - Execute requests/queries.
  - Return raw results in a simple format (list-of-lists, dict, or DataFrame if convenient).
- Keep network I/O and retry logic here. Make the function easy to mock in tests.

3. Implement a client/helper if required

- Location: `utils/connector/<backend>/module.py`.
- Use this file for SDK clients, session management, and auth token refresh logic.

4. Add the public tool function

- Location: `tools/<backend>/<backend>_tools.py`.
- Responsibilities:
  - Validate/normalize inputs.
  - Call provider functions.
  - Convert raw results to `pandas.DataFrame` or `dict`.
  - Catch exceptions, log context, and re-raise `RuntimeError`.

5. Testing

- Create a `tests/` directory (if not present) and add tests for the provider and tool layers.
- Use `pytest` and `unittest.mock` to patch network calls.
- Minimum tests:
  - Happy path: provider returns expected data and the tool returns the expected DataFrame/dict.
  - Empty result: confirm the tool returns an empty DataFrame or `None` as specified.
  - Error propagation: provider raises an exception; the tool raises `RuntimeError`.

Example unit test (pytest style)

```python
# tests/test_google_sheet_tool.py
from unittest.mock import patch
import pandas as pd

from tools.google_sheet.google_sheet_tools import query_google_sheet_data

@patch("utils.connector.google_sheet.providers.fetch_google_sheet_as_df")
def test_query_google_sheet_data(mock_fetch):
    mock_fetch.return_value = pd.DataFrame({"a": [1, 2]})

    df = query_google_sheet_data("dummy_id", range_name="Sheet1!A1:B2")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert list(df.columns) == ["a"]
```

6. Documentation and examples

- Add example usage to `documents/USAGE.md` for public-facing functions.
- Add a clear docstring to the new tool function describing inputs, outputs, and example usage.

7. Linting and pre-commit

- Follow the project's style (black/flake8/isort if configured). Run linters locally before pushing.

8. Open a PR

- Include a short description of the new tool, the contract (inputs/outputs), and how to test it.
- Add reviewers for the backend and a maintainer.

API design tips

- Name functions clearly and consistently: verb_noun (e.g., `query_clickhouse_logic`, `fetch_google_sheet_as_df`).
- Keep the tool function surface minimal and well-documented.
- Add logging at DEBUG level for request/response content but avoid logging secrets.

Common pitfalls

- Embedding credentials in code. Always use environment variables.
- Returning raw SDK objects from tool functions — convert results to DataFrame/dict to keep outputs predictable.


