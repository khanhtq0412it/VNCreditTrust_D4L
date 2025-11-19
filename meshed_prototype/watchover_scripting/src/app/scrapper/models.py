from __future__ import annotations


from pydantic import BaseModel


class TinResult(BaseModel):
    url: str
    html_source: str
    text_source: str


class ProductResult(BaseModel):
    url: str
    html_source: str
    text_source: str
