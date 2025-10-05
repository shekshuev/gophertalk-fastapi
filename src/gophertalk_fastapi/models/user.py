from typing import Optional, Self

from pydantic import Field, field_validator, model_validator
from pydantic.dataclasses import dataclass

from .validators import name_validator, password_validator, username_validator


@dataclass
class CreateUserDto:
    user_name: str
    password_hash: str
    first_name: str
    last_name: str


@dataclass
class ReadUserDto:
    id: int
    user_name: str
    first_name: str
    last_name: str
    status: int
    created_at: str
    updated_at: str


@dataclass
class ReadAuthUserDataDto:
    id: int
    user_name: str
    password_hash: str
    status: int


@dataclass
class UpdateUserDto:
    user_name: Optional[str] = Field(None)
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    password: Optional[str] = Field(None)
    password_confirm: Optional[str] = Field(None)
    password_hash: Optional[str] = Field(None)

    @field_validator("user_name", mode="after")
    @classmethod
    def validate_username(cls, value: str) -> str:
        return username_validator(value)

    @field_validator("password", mode="after")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return password_validator(value)

    @field_validator("first_name", "last_name", mode="after")
    @classmethod
    def validate_names(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return name_validator(value)

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.password != self.password_confirm:
            raise ValueError("Passwords does not match")
        return self
