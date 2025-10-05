import pytest
from pydantic import ValidationError

from gophertalk_fastapi.models.user import (
    CreateUserDto,
    ReadAuthUserDataDto,
    ReadUserDto,
    UpdateUserDto,
)


def test_create_user_dto_valid():
    """
    Should create a valid `CreateUserDto` when all fields are provided.
    """
    dto = CreateUserDto(
        user_name="john_doe",
        password_hash="hashed_pass",
        first_name="John",
        last_name="Doe",
    )
    assert dto.user_name == "john_doe"
    assert dto.password_hash == "hashed_pass"
    assert dto.first_name == "John"


def test_read_user_dto_valid():
    """
    Should instantiate a `ReadUserDto` with valid values.
    """
    dto = ReadUserDto(
        id=1,
        user_name="jane",
        first_name="Jane",
        last_name="Smith",
        status=1,
        created_at="2025-10-05T00:00:00Z",
        updated_at="2025-10-05T00:00:00Z",
    )
    assert dto.id == 1
    assert dto.user_name == "jane"
    assert dto.status == 1
    assert dto.created_at.endswith("Z")


def test_read_auth_user_data_dto_valid():
    """
    Should instantiate `ReadAuthUserDataDto` with proper fields.
    """
    dto = ReadAuthUserDataDto(
        id=42, user_name="alice", password_hash="hash123", status=1
    )
    assert dto.id == 42
    assert dto.password_hash == "hash123"


def test_update_user_dto_valid_partial():
    """
    Should allow partial updates with some optional fields set.
    """
    dto = UpdateUserDto(
        user_name="new_user",
        first_name="New",
        last_name="Name",
        password="Qwerty1!",
        password_confirm="Qwerty1!",
    )
    assert dto.user_name == "new_user"
    assert dto.password == "Qwerty1!"
    assert dto.password_confirm == "Qwerty1!"


def test_update_user_dto_passwords_do_not_match():
    """
    Should raise ValidationError when passwords do not match.
    """
    with pytest.raises(ValidationError) as e:
        UpdateUserDto(password="Qwerty1!", password_confirm="Different1!")
    assert "Passwords does not match" in str(e.value)


def test_update_user_dto_invalid_username():
    """
    Should raise ValidationError when username fails custom validator.
    """
    with pytest.raises(ValidationError):
        UpdateUserDto(user_name="bad name")  # space not allowed


def test_update_user_dto_invalid_password():
    """
    Should raise ValidationError when password fails security pattern.
    """
    with pytest.raises(ValidationError):
        UpdateUserDto(password="weak", password_confirm="weak")


def test_update_user_dto_ignores_none_fields():
    """
    Should not raise ValidationError if optional fields are None.
    """
    dto = UpdateUserDto(
        user_name=None,
        first_name=None,
        last_name=None,
        password=None,
        password_confirm=None,
    )
    assert dto.user_name is None
    assert dto.password is None
