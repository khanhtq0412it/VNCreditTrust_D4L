from __future__ import annotations

from enum import StrEnum

from app.utils import snake_to_pascal_case
from app.settings import get_settings


def get_orgs() -> dict[str, str]:
    settings = get_settings()
    orgs = settings.orgs
    mapping = {snake_to_pascal_case(org.name): org.name for org in orgs}

    return mapping


OrgKind = StrEnum("OrgKind", get_orgs())
