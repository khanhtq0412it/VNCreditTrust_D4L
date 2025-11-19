from __future__ import annotations

from urllib.parse import urlparse


def snake_to_pascal_case(filename: str) -> str:
    """Convert snake/kebab to PascalCase."""

    parts = filename.replace("-", "_").split("_")
    return "".join(p.capitalize() for p in parts)


def is_url(input: str) -> bool:
    try:
        result = urlparse(input)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
