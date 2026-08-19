from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class URLCreate(BaseModel):
    original_url: HttpUrl
    custom_code: str | None = None


class URLResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    short_code: str
    original_url: str
    short_url: str | None = None
    is_active: bool
    created_at: datetime


class URLRedirect(BaseModel):
    short_code: str
    original_url: str
