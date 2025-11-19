import click

from app.cli.scrape import scrape
from app.settings import get_settings


def create_cli() -> click.Group:
    settings = get_settings()

    @click.group(help=settings.app.description)
    @click.version_option(
        version=settings.app.version,
        prog_name=settings.app.name,
    )
    def cli():
        pass

    cli.add_command(scrape, name="scrape")

    return cli
