from datetime import datetime
from typing import Optional

from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass
class CreatePostDto:
    text: str = Field(..., min_length=1, max_length=280)
    reply_to_id: Optional[int] = Field(None, ge=1)
    user_id: int = Field(None, ge=1)


@dataclass
class FilterPostDto:
    search: Optional[str] = None
    owner_id: Optional[int] = Field(None, ge=1)
    user_id: Optional[int] = Field(None, ge=1)
    reply_to_id: Optional[int] = Field(None, ge=1)
    limit: Optional[int] = Field(None, ge=1)
    offset: Optional[int] = Field(None, ge=0)


@dataclass
class ReadPostUserDto:
    id: int
    user_name: str
    first_name: str
    last_name: str


@dataclass
class ReadPostDto:
    id: int
    text: str
    user_id: int
    reply_to_id: Optional[int]
    created_at: datetime
    likes_count: Optional[int] = Field(None)
    views_count: Optional[int] = Field(None)
    user: Optional[ReadPostUserDto] = Field(None)
