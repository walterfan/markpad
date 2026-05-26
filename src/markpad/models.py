from __future__ import annotations

from pydantic import BaseModel, Field


class FileEntry(BaseModel):
    path: str
    name: str
    directory: str
    size: int
    mtime: float = Field(description="Unix timestamp in seconds.")


class FileContent(BaseModel):
    path: str
    content: str
    mtime: float


class RenderRequest(BaseModel):
    content: str
    path: str | None = None


class RenderResponse(BaseModel):
    html: str


class AppConfigResponse(BaseModel):
    translate_available: bool
    llm_model: str | None = None


class TranslateRequest(BaseModel):
    content: str
    target_language: str = "Chinese"


class TranslateResponse(BaseModel):
    content: str


class SaveRequest(BaseModel):
    path: str
    content: str


class SaveResponse(BaseModel):
    path: str
    mtime: float
