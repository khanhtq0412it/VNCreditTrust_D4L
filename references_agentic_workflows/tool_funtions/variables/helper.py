"""
helper.py

Configuration helper module for loading environment variables.

- If a `.env` file exists in the project root, it will be loaded automatically (for local/dev use).
- If no `.env` file exists, the module will fall back to system environment variables (for production/CI/CD use).
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import Type, Dict, Any, List


# === [1] Load .env file if present ===
base_dir = Path(__file__).resolve().parent.parent  # e.g., /tool-function/variables/..
env_path = base_dir / ".env"

if env_path.exists():
    load_dotenv(env_path)


# === [2] Base configuration class ===
class BaseConfig:
    """
    Base configuration class for loading environment variables.

    Behavior:
        - If `.env` exists, values are loaded from it.
        - Otherwise, values are read directly from system environment variables.

    Attributes:
        VARIABLES (list[str]): List of environment variable names to load.

    Methods:
        - load(mode='basic'): Load all variables defined in `VARIABLES`.
        - get_variable(name, default_value=None, deserialize_json=False): Retrieve a variable.
    """

    VARIABLES = []  # List of environment variable names to be loaded

    @classmethod
    def load(cls, mode: str = 'basic') -> Dict[str, Any]:
        """
        Load environment variables defined in the `VARIABLES` list.

        Args:
            mode (str): Loading mode (currently only 'basic' is supported).

        Returns:
            dict: A dictionary containing variable names and their values.

        Raises:
            ValueError: If an unsupported mode is provided.
        """
        if mode != 'basic':
            raise ValueError("Invalid 'mode'. Only 'basic' is supported.")

        config = {}
        for var in cls.VARIABLES:
            value = cls.get_variable(var)
            if value is None:
                print(f"⚠️ Warning: environment variable '{var}' is not set.")
            config[var] = value
        return config

    @staticmethod
    def get_variable(name: str, default_value=None, deserialize_json=False):
        """
        Retrieve an environment variable value.

        Args:
            name (str): The environment variable name.
            default_value (any, optional): Fallback value if not found. Defaults to None.
            deserialize_json (bool, optional): If True, parse the value as JSON.

        Returns:
            str | dict | None: The environment variable value (optionally parsed as JSON).

        Raises:
            ValueError: If JSON deserialization fails.
        """
        value = os.getenv(name, default_value)
        if deserialize_json and value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON format in environment variable '{name}'.")
        return value


# === [3] Utility class for loading multiple configs ===
class ConfigLoader:
    """
    Utility class for loading environment variables from one or multiple configuration classes.

    Example
    -------
    >>> from variables.helper import ConfigLoader
    >>> from variables.clickhouse import ClickHouseConfig

    # Load a single config
    >>> clickhouse_cfg = ConfigLoader.load_single(ClickHouseConfig)
    >>> print(clickhouse_cfg["CLICKHOUSE_HOST"])

    # Load multiple configs
    >>> merged = ConfigLoader.load_multiple([ClickHouseConfig, AnotherConfig])
    >>> print(merged)
    """

    @staticmethod
    def load_single(config_cls: Type[BaseConfig]) -> Dict[str, Any]:
        """
        Load environment variables from a single configuration class.

        Args:
            config_cls (Type[BaseConfig]): The configuration class.

        Returns:
            dict: Dictionary of variable names and their values.
        """
        return config_cls.load()

    @staticmethod
    def load_multiple(config_classes: List[Type[BaseConfig]]) -> Dict[str, Any]:
        """
        Load and merge environment variables from multiple configuration classes.

        Args:
            config_classes (list[Type[BaseConfig]]): List of configuration classes.

        Returns:
            dict: Merged dictionary containing all environment variables.
                  Later classes override earlier ones on key conflicts.
        """
        merged = {}
        for cfg_cls in config_classes:
            merged.update(cfg_cls.load())
        return merged
