from typing import Optional, Self

from pydantic import Field, field_validator, model_validator
from pydantic.dataclasses import dataclass

from .validators import name_validator, password_validator, username_validator


@dataclass
class LoginUserDto:
    user_name: str
    password: str

    @field_validator("user_name", mode="after")
    @classmethod
    def validate_username(cls, value: str) -> str:
        return username_validator(value)

    @field_validator("password", mode="after")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return password_validator(value)


@dataclass
class RegisterUserDto:
    user_name: str
    password: str
    password_confirm: str
    first_name: Optional[str] = Field(None, min_length=1, max_length=30)
    last_name: Optional[str] = Field(None, min_length=1, max_length=30)

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


@dataclass
class ReadTokenDto:
    access_token: str
    refresh_token: str
