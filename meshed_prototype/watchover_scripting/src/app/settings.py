from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal
from glob import glob

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    JsonConfigSettingsSource,
    SettingsConfigDict,
    PyprojectTomlConfigSettingsSource,
)

from app import constants
from app.logger.enums import LogLevel


PYPROJECT_TOML_PATH = constants.PROJECT_DIR.joinpath("pyproject.toml")
SETTINGS_JSON_PATH = constants.PROJECT_DIR.joinpath("settings.json")
ORG_JSON_PATHS = glob(f"{constants.PROJECT_DIR}/*.json")


class OrgSettings(BaseModel):
    name: str
    base_url: str
    product_list_url_path: str
    product_info_prune_xpaths: list[str]
    tin_url: str
    with_captcha: bool
    with_sleep: bool
    product_list_action: Literal["click"] | None
    product_list_query: str | None
    product_list_tab_query: str | None


class WorkerSettings(BaseModel):
    max_num: int = 8


class LoggingSettings(BaseModel):
    level: LogLevel = LogLevel.Info
    time_format: str = "%Y-%m-%d %H:%M:%S"
    utc: bool = False


class AppSettings(BaseModel):
    name: str = "vncreditrust-watchtower"
    description: str = "The watchtower component for VnCrediTrust"
    version: str = "0.1.0"


class Settings(BaseSettings):
    app: Annotated[AppSettings, Field(alias="project")] = AppSettings()
    worker: WorkerSettings = WorkerSettings()
    logging: LoggingSettings = LoggingSettings()
    orgs: list[OrgSettings] = []

    model_config = SettingsConfigDict(
        extra="ignore",
        pyproject_toml_table_header=(),
        toml_file=PYPROJECT_TOML_PATH,
        json_file=SETTINGS_JSON_PATH,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            PyprojectTomlConfigSettingsSource(
                settings_cls,
            ),
            JsonConfigSettingsSource(
                settings_cls,
            ),
        )


@lru_cache(typed=True, maxsize=1)
def get_settings() -> Settings:
    return Settings()
