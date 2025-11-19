from __future__ import annotations

from typing import TYPE_CHECKING

from app.logger.factory import get_logger

if TYPE_CHECKING:
    from pydoll.browser.chromium.base import Browser


class ContextPool:
    def __init__(self, browser: Browser, size: int) -> None:
        self.browser = browser
        self.size = size

        self.contexts = []
        self.in_use = set()

        self.logger = get_logger("context_pool")

    async def init(self) -> None:
        for _ in range(self.size):
            context_id = await self.browser.create_browser_context()
            self.contexts.append(context_id)
        self.logger.info("Context pool initialized", contexts=len(self.contexts))

    async def acquire(self):
        for context_id in self.contexts:
            if context_id not in self.in_use:
                self.in_use.add(context_id)
                return context_id
        raise Exception("No available contexts in pool")

    def release(self, context_id) -> None:
        self.in_use.discard(context_id)

    async def cleanup(self):
        for context_id in self.contexts:
            await self.browser.delete_browser_context(context_id)
