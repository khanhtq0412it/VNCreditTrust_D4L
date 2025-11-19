from __future__ import annotations

from typing import TYPE_CHECKING

from app.settings import get_settings
from app.scrapper.enums import OrgKind

if TYPE_CHECKING:
    from app.settings import OrgSettings

settings = get_settings()

ORG_SETTINGS_MAP = {o.name: o for o in settings.orgs}


def get_org_settings(name: OrgKind) -> OrgSettings:
    return ORG_SETTINGS_MAP[name]
