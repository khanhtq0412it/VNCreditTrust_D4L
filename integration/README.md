# Integration — Data-For-Life

This repository contains small tooling and examples for moving and validating a
structured dataset and streaming connectors used in the Data-For-Life / VN
CreditTrust projects.

Top-level layout
- `python-batching/` — utilities to generate metadata, validate JSON key sets,
  and upload data to MinIO/S3-compatible storage.
- `kafka-streaming/` — example Kafka Connect connector configs and producer
  jobs. Subfolders:
  - `source-connector/` — producer job(s), manifests and helper Kubernetes
    resources used for testing and development.
  - `sink-connector/` — example sink connector configurations (ClickHouse, S3).

Quick start
1. Install Python dependencies (recommended inside a virtualenv):

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

2. Generate metadata for a local dataset (example):

```bash
python python-batching/generate_metadata.py /path/to/data /path/to/metadata.csv
```

3. Validate JSON keys across units:

```bash
python python-batching/validate_json.py /path/to/metadata.csv
```

4. Upload content to MinIO (configure credentials first, see `env.local.example`):

```bash
export MINIO_ENDPOINT=host:port
export MINIO_ACCESS_KEY=...
export MINIO_SECRET_KEY=...
export MINIO_BUCKET=vncredittrust-lake
python python-batching/upload_to_minio.py --root-dir /path/to/data --prefix reference/2025-11-16/
```

Notes
- Do not commit secrets into source control. Use `env.local` / CI secrets.
- This repo contains example connector YAMLs and Dockerfiles used for
  development. Review and adapt to your environment before deploying in
  production.

License: MIT (see `LICENSE`)

