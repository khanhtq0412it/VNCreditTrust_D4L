from __future__ import annotations

from typing import TYPE_CHECKING

import trafilatura
from minify_html import minify

if TYPE_CHECKING:
    from typing import Literal


class Extractor:
    def __init__(self) -> None:
        self.favor_recall = True
        self.fast = True

    def extract(
        self,
        page_source: str,
        format: Literal["html", "txt"],
        prune_xpath: str | list[str] | None,
    ) -> str:
        extracted_source = trafilatura.extract(
            page_source,
            output_format=format,
            favor_recall=self.favor_recall,
            prune_xpath=prune_xpath,
        )
        if extracted_source is None:
            return ""

        minified = minify(extracted_source)

        return minified
