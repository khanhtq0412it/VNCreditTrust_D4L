# Tool-Function Repository — Architecture Overview

This document summarizes the architecture and directory structure for the `tool-function` repository.

## Purpose

The repository exposes a collection of small, focused "tool" functions that provide programmatic access to external data systems (ClickHouse, Google Sheets, PostgreSQL, etc.). These tools are intended to be consumed by automation agents, LLM-driven workflows, or orchestration systems that need safe access to data and metadata.

## High-level architecture

- tools/
  - Contains top-level, user-facing functions organized by backend system (clickhouse, google_sheet, postgres). Each module implements a small set of pure functions that act as the public contract for the repository.
  - Functions translate user inputs into queries or connector calls and return pandas DataFrames or simple Python primitives.

- utils/connector/
  - Supplies connector implementations for external systems. Each connector (clickhouse, google_sheet, postgres) exposes a `providers.py` helper that implements the lower-level I/O: authentication, request execution, and result shaping.
  - Connectors are intentionally thin and focused, enabling easy mocking and unit testing.

- variables/
  - Centralized configuration definitions and helpers. Config classes list expected environment variables (service account JSON, connection strings, host/port, etc.). Use `variables.helper.ConfigLoader` to load typed configuration.

- documents/
  - Markdown documentation (this folder). Contains architecture, usage, contribution, and deployment guides.

- plugins/
  - (Optional) Placeholder for third-party or extension hooks.

- local.env / .env / Dockerfile / .gitlab-ci.yml
  - Deployment and CI configuration. Environment files contain runtime variables; Dockerfile provides containerization; CI file contains job definitions.

## Data flow

1. Caller invokes a function from `tools/<backend>/*_tools.py` with structured parameters.
2. Tool function validates inputs and calls a corresponding provider in `utils/connector/<backend>/providers.py`.
3. The provider constructs requests (SQL, HTTP) using connector helper classes in `utils/connector/<backend>/module.py` and possible `helper.py` utilities.
4. Raw responses are transformed into pandas DataFrame (for tabular results) or Python primitives before returning to the caller.

## Error handling and logging

- Tool functions catch low-level exceptions from providers, log an informative message, and re-raise a `RuntimeError` with context.
- Providers may perform minimal error handling and typically bubble exceptions up to tools.

## Design goals

- Small surface area: each tool implements one focused capability.
- Testability: connectors abstract network I/O for easier mocking.
- Agent-friendly outputs: tools return DataFrames and simple dicts suitable for prompt-based agents.

## Where to look first

- Entry points (user-facing): `tools/` directory.
- Connector implementations: `utils/connector/*/providers.py` and `module.py`.
- Configuration: `variables/` modules and `local.env`.
- CI / deployment: `.gitlab-ci.yml` and `Dockerfile`.


