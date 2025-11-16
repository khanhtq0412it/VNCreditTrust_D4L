"""
upload_to_minio.py

Small utility to upload a directory tree to a MinIO/S3-compatible bucket while
preserving the local directory structure under a configurable prefix.

Credentials and endpoint are read from environment variables by default to keep
secrets out of source control. A simple CLI is provided for manual runs.
"""
from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional

from minio import Minio

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("upload_to_minio")


def make_minio_client(endpoint: str, access_key: str, secret_key: str, secure: bool = False) -> Minio:
    """Create and return a configured Minio client.

    Do not store credentials in source control; prefer environment variables
    or secret management in CI.
    """
    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


def upload_tree(client: Minio, root_dir: str | Path, bucket: str, prefix: str = "") -> int:
    """Upload files under root_dir to the given bucket using the specified prefix.

    Returns the number of objects uploaded.
    """
    root = Path(root_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"root_dir not found: {root}")

    uploads = 0
    if not client.bucket_exists(bucket):
        logger.info("Bucket '%s' does not exist; creating it.", bucket)
        client.make_bucket(bucket)

    for org in sorted(p for p in root.iterdir() if p.is_dir()):
        for unit in sorted(p for p in org.iterdir() if p.is_dir()):
            for f in sorted(p for p in unit.iterdir() if p.is_file()):
                remote_path = f"{prefix.rstrip('/')}/{org.name}/{unit.name}/{f.name}".lstrip('/')
                logger.info("Uploading %s → %s/%s", f, bucket, remote_path)
                client.fput_object(bucket_name=bucket, object_name=remote_path, file_path=str(f))
                uploads += 1
    logger.info("Upload completed (%d objects)", uploads)
    return uploads


def main(
    root_dir: Optional[str] = None,
    bucket: Optional[str] = None,
    prefix: str = "",
    endpoint: Optional[str] = None,
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    secure: bool = False,
):
    endpoint = endpoint or os.environ.get("MINIO_ENDPOINT")
    access_key = access_key or os.environ.get("MINIO_ACCESS_KEY")
    secret_key = secret_key or os.environ.get("MINIO_SECRET_KEY")
    bucket = bucket or os.environ.get("MINIO_BUCKET")
    root_dir = root_dir or os.environ.get("MINIO_ROOT_DIR", "./data")

    if not all([endpoint, access_key, secret_key, bucket]):
        raise ValueError("MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY and MINIO_BUCKET must be provided")

    client = make_minio_client(endpoint, access_key, secret_key, secure=secure)
    count = upload_tree(client, root_dir, bucket, prefix)
    logger.info("Total uploaded objects: %d", count)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Upload data tree to MinIO/S3")
    parser.add_argument("--root-dir", default=os.environ.get("MINIO_ROOT_DIR", "./data"), help="Local root directory to upload")
    parser.add_argument("--bucket", default=os.environ.get("MINIO_BUCKET"), help="Target bucket name")
    parser.add_argument("--prefix", default=os.environ.get("MINIO_PREFIX", ""), help="Prefix inside the bucket")
    parser.add_argument("--endpoint", default=os.environ.get("MINIO_ENDPOINT"), help="MinIO endpoint host:port")
    parser.add_argument("--access-key", default=os.environ.get("MINIO_ACCESS_KEY"), help="MinIO access key")
    parser.add_argument("--secret-key", default=os.environ.get("MINIO_SECRET_KEY"), help="MinIO secret key")
    parser.add_argument("--secure", action="store_true", help="Use HTTPS when connecting to MinIO")
    args = parser.parse_args()

    main(
        root_dir=args.root_dir,
        bucket=args.bucket,
        prefix=args.prefix,
        endpoint=args.endpoint,
        access_key=args.access_key,
        secret_key=args.secret_key,
        secure=args.secure,
    )
