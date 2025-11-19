import logging
from enum import StrEnum


class LogFormat(StrEnum):
    Console = "console"
    Json = "Json"


class LogLevel(StrEnum):
    Debug = "debug"
    Info = "info"
    Warning = "warning"
    Error = "error"
    Critical = "critical"

    @property
    def numeric(self) -> int:
        return {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }[self.value]
