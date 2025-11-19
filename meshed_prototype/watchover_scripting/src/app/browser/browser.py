from __future__ import annotations

import asyncio

from app.browser.options import get_brower_options
from app.browser.tab_pool import TabPool
from app.logger.factory import get_logger
from app.scrapper.enums import OrgKind
from app.scrapper.registry import get_org_settings
from app.scrapper.scrapper import Scrapper
from app.settings import get_settings


class Browser:
    def __init__(self, orgs: list[OrgKind]) -> None:
        self.orgs = orgs

        self.settings = get_settings()
        self.options = get_brower_options()

        self.logger = get_logger("browser")

    async def run(self) -> None:
        num_tabs = len(self.orgs)

        await self.logger.ainfo(
            "Starting run",
            tasks=num_tabs,
            max_tabs=self.settings.worker.max_num,
            orgs=[o.name for o in self.orgs],
        )

        async with TabPool(
            browser_options=self.options,
            num_tabs=num_tabs,
            max_tabs=self.settings.worker.max_num,
        ) as tabs:
            tasks: list[asyncio.Task[None]] = []

            for index, org in enumerate(self.orgs):
                tab = tabs[index % num_tabs]
                org_settings = get_org_settings(org)
                scrapper = Scrapper(org_settings)
                tasks.append(asyncio.create_task(scrapper.start(tab)))

            await self.logger.ainfo("All tasks dispatched", count=len(tasks))

            await asyncio.gather(*tasks)

        await self.logger.ainfo("Run completed", tasks=num_tabs)
