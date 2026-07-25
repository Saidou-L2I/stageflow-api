"""Parametres de pagination communs a tous les endpoints de liste."""
from typing import Annotated, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

from app.core.config import settings

T = TypeVar("T")


class PageParams(BaseModel):
    skip: int = 0
    limit: int = settings.DEFAULT_PAGE_SIZE


def pagination_params(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=settings.MAX_PAGE_SIZE)] = settings.DEFAULT_PAGE_SIZE,
) -> PageParams:
    return PageParams(skip=skip, limit=limit)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int
