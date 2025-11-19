from __future__ import annotations

import click
import uvloop

from app.scrapper.enums import OrgKind
from app.browser.browser import Browser


def orgkind_choice(value: str) -> OrgKind:
    try:
        return OrgKind(value)
    except ValueError:
        valid = ", ".join([k.value for k in OrgKind])
        raise click.BadParameter(f"Invalid org '{value}'. Valid: {valid}")


@click.command(help="Run the scrapper for supported orgs.")
@click.option(
    "--all",
    "run_all",
    is_flag=True,
    help="Run the scrapper for all orgs and ignore the org list.",
)
@click.argument(
    "orgs",
    nargs=-1,
    type=orgkind_choice,
)
@click.pass_context
def scrape(ctx: click.Context, run_all: bool, orgs: list[OrgKind]) -> None:
    """
    Run scrapper for specific orgs, or run all of them.

    Examples:
        scrape fecredit
        scrape fecredit techombank
        scrape --all

    If you do not provide any orgs, guidance will be shown.
    """

    if run_all:
        org_list = list(OrgKind)
    else:
        if not orgs:
            click.echo(ctx.get_help())
            ctx.exit(1)

        org_list = orgs

    browser = Browser(org_list)
    uvloop.run(browser.run())
