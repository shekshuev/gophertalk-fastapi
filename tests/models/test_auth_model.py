import pytest
from pydantic import ValidationError

from gophertalk_fastapi.models.auth import LoginUserDto, RegisterUserDto


def test_login_user_dto_valid():
    """Should create a valid LoginUserDto when inputs are correct."""
    dto = LoginUserDto(user_name="john_doe", password="StrongPass123!")
    assert dto.user_name == "john_doe"
    assert dto.password == "StrongPass123!"


def test_login_user_dto_invalid_username():
    """Should raise ValidationError for invalid username."""
    with pytest.raises(ValidationError):
        LoginUserDto(user_name="xx", password="StrongPass123")


def test_register_user_dto_passwords_match():
    """Should validate when passwords match."""
    dto = RegisterUserDto(
        user_name="alice",
        password="ValidPass123!",
        password_confirm="ValidPass123!",
        first_name="Alice",
        last_name="Smith",
    )
    assert dto.password == dto.password_confirm


def test_register_user_dto_passwords_do_not_match():
    """Should raise ValueError if passwords don't match."""
    with pytest.raises(ValidationError) as exc:
        RegisterUserDto(
            user_name="bob_wilson",
            password="Password123!",
            password_confirm="Mismatch123!",
        )
    assert "Passwords does not match" in str(exc.value)


def test_register_user_dto_invalid_name():
    """Should raise ValidationError if name contains invalid characters."""
    with pytest.raises(ValidationError):
        RegisterUserDto(
            user_name="charlie",
            password="ValidPass123",
            password_confirm="ValidPass123",
            first_name="A!ice",
        )
