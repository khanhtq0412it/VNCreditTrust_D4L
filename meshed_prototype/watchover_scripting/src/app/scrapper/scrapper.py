from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from slugify import slugify

from app.extractor import Extractor
from app.scrapper.models import ProductResult, TinResult
from app.utils import is_url

if TYPE_CHECKING:
    from pydoll.browser.tab import Tab
    from app.settings import OrgSettings


class Scrapper:
    def __init__(self, org: OrgSettings) -> None:
        self.org = org
        self.extractor = Extractor()

    async def start(self, tab: Tab) -> None:
        if not self.org.base_url:
            products = []
        else:
            urls = await self._get_product_urls(tab)
            products = [await self._get_product(tab, url) for url in urls]

        tin = await self._get_tin(tab)
        await self._write(products, tin)

    async def _get_product_urls(self, tab: Tab) -> set[str]:
        product_list_url = self.org.base_url + self.org.product_list_url_path

        if self.org.product_list_query is None:
            return {product_list_url}

        await self._go_to(tab, product_list_url)
        urls: set[str] = set()

        if self.org.product_list_tab_query:
            urls |= await self._urls_with_tabs(
                tab,
                product_list_url,
                self.org.product_list_query,
                self.org.product_list_tab_query,
            )
        else:
            urls |= await self._urls_single(
                tab, product_list_url, self.org.product_list_query
            )

        return urls

    async def _urls_single(self, tab: Tab, list_url: str, query: str) -> set[str]:
        urls: set[str] = set()

        els = await tab.query(query, find_all=True)

        if self.org.product_list_action == "click":
            for idx in range(len(els)):
                els = await tab.query(query, find_all=True)
                el = els[idx]
                if el.tag_name == "":
                    continue
                await el.click()
                await asyncio.sleep(5)
                urls.add(await tab.current_url)
                await self._go_to(tab, list_url)
                await tab.scroll.to_bottom()
        else:
            for el in els:
                href = el.get_attribute("href")
                if href:
                    urls.add(href if is_url(href) else self.org.base_url + href)

        return urls

    async def _urls_with_tabs(
        self, tab: Tab, list_url: str, query: str, tab_query: str
    ) -> set[str]:
        urls: set[str] = set()

        tab_els = await tab.query(tab_query, find_all=True)

        for t_idx in range(len(tab_els)):
            tab_els = await tab.query(tab_query, find_all=True)
            t = tab_els[t_idx]
            if await t.is_visible():
                await t.click()
            else:
                href = t.get_attribute("href")
                if href:
                    await self._go_to(
                        tab, href if is_url(href) else self.org.base_url + href
                    )
            await asyncio.sleep(5)
            await tab.scroll.to_bottom()

            link_els = await tab.query(query, find_all=True)

            if self.org.product_list_action == "click":
                for l_idx in range(len(link_els)):
                    link_els = await tab.query(query, find_all=True)
                    link = link_els[l_idx]
                    await link.click()
                    await asyncio.sleep(5)
                    urls.add(await tab.current_url)
                    await self._go_to(tab, list_url)
                    await asyncio.sleep(5)
                    tab_els = await tab.query(tab_query, find_all=True)

                    if await tab_els[t_idx].is_visible():
                        await tab_els[t_idx].click()
                    else:
                        href = tab_els[t_idx].get_attribute("href")
                        if href:
                            await self._go_to(
                                tab, href if is_url(href) else self.org.base_url + href
                            )

                    await tab.scroll.to_bottom()
            else:
                for el in link_els:
                    href = el.get_attribute("href")
                    if href:
                        urls.add(href if is_url(href) else self.org.base_url + href)

                await self._go_to(tab, list_url)
                await asyncio.sleep(5)

        return urls

    async def _get_product(self, tab: Tab, url: str) -> ProductResult:
        await self._go_to(tab, url)
        src = await tab.page_source
        html = self.extractor.extract(
            src, format="html", prune_xpath=self.org.product_info_prune_xpaths
        )
        txt = self.extractor.extract(
            src, format="txt", prune_xpath=self.org.product_info_prune_xpaths
        )
        return ProductResult(url=url, html_source=html, text_source=txt)

    async def _get_tin(self, tab: Tab) -> TinResult:
        await tab.go_to(self.org.tin_url)
        src = await tab.page_source
        html = self.extractor.extract(
            src, format="html", prune_xpath=self.org.product_info_prune_xpaths
        )
        txt = self.extractor.extract(
            src, format="txt", prune_xpath=self.org.product_info_prune_xpaths
        )
        return TinResult(url=self.org.tin_url, html_source=html, text_source=txt)

    async def _write(self, products: list[ProductResult], tin: TinResult) -> None:
        out = Path("data").joinpath(self.org.name)
        out.mkdir(parents=True, exist_ok=True)

        for p in products:
            slug = slugify(p.url)[:250]
            out.joinpath(f"product_{slug}.html").write_text(
                p.html_source, encoding="utf-8"
            )
            out.joinpath(f"product_{slug}.txt").write_text(
                p.text_source, encoding="utf-8"
            )

        out.joinpath("tin.html").write_text(tin.html_source, encoding="utf-8")
        out.joinpath("tin.txt").write_text(tin.text_source, encoding="utf-8")

    async def _go_to(self, tab: Tab, url: str) -> None:
        if self.org.with_captcha:
            async with tab.expect_and_bypass_cloudflare_captcha():
                await tab.go_to(url)
        else:
            await tab.go_to(url)

        if self.org.with_sleep:
            await asyncio.sleep(5)
