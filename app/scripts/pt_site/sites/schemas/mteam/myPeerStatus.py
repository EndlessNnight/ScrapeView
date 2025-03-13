from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Data(BaseModel):
    leecher: str
    seeder: str


class ResponseModel(BaseModel):
    message: Optional[str] = None
    data: Optional[Data] = None
    code: Optional[str] = None
