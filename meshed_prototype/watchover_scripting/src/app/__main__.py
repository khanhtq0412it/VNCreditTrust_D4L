from __future__ import annotations

import sys
from pathlib import Path
from typing import NoReturn


def setup_environment() -> None:
    current_path = Path(__file__).parent.parent.resolve()
    sys.path.append(str(current_path))


def setup() -> None:
    setup_environment()

    from app.logger.setup import setup_logging

    setup_logging()


def run_cli() -> NoReturn:
    setup()
    from app.logger.factory import get_logger

    logger = get_logger("main")

    try:
        from app.cli.main import create_cli

        cli = create_cli()
        sys.exit(cli())
    except Exception as exc:
        logger.exception("Unexpected error", error=exc, stack_info=True)
        sys.exit(1)
