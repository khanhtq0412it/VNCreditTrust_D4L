from __future__ import annotations

from typing import TYPE_CHECKING

from app.logger.factory import get_logger
from pydoll.browser import Chrome

from app.browser.context_pool import ContextPool

if TYPE_CHECKING:
    from typing import Optional

    from pydoll.browser.chromium.base import Browser
    from pydoll.browser.options import ChromiumOptions
    from pydoll.browser.tab import Tab


class TabPool:
    def __init__(
        self, browser_options: ChromiumOptions, num_tabs: int, max_tabs: int
    ) -> None:
        self.browser_options = browser_options
        self.num_tabs = max(1, min(num_tabs, max_tabs))

        self.browser: Optional[Browser] = None
        self.context_pool: Optional[ContextPool] = None
        self.workers: list[Tab] = []

        self.logger = get_logger("tab_pool")

    async def __aenter__(self) -> list[Tab]:
        self.browser = Chrome(self.browser_options)

        init_tab = await self.browser.start()
        await self.logger.ainfo("The browser is started")

        extra_tabs: list[Tab] = []

        # Only create a context pool if we actually need extra workers
        if self.num_tabs > 1:
            self.context_pool = ContextPool(self.browser, self.num_tabs - 1)
            await self.context_pool.init()

            extra_workers = self.num_tabs - 1
            for _ in range(extra_workers):
                ctx = await self.context_pool.acquire()
                extra_tabs.append(await self.browser.new_tab(ctx))

        self.workers = [init_tab] + extra_tabs
        await self.logger.ainfo("Tab pool initialized", workers=self.num_tabs)

        return self.workers

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            if self.context_pool is not None:
                try:
                    await self.context_pool.cleanup()
                finally:
                    self.context_pool = None
        finally:
            if self.browser is not None:
                try:
                    await self.browser.stop()
                finally:
                    self.browser = None
                    self.workers = []
