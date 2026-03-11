from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateUiRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User natural-language query")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: str | None = None
