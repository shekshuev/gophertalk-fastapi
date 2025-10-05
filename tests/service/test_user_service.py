import bcrypt
import pytest

from gophertalk_fastapi.models.user import ReadUserDto, UpdateUserDto
from gophertalk_fastapi.repository.user_repository import UserNotFoundError


def test_get_all_users_success(user_service, mock_user_repository):
    """
    Test that `get_all()` returns a list of `ReadUserDto` objects.

    Steps:
      1. Mock repository to return a list of users.
      2. Call `get_all()` with limit and offset.
      3. Assert that result matches expected data and repository called correctly.
    """
    mock_user_repository.get_all_users.return_value = [
        ReadUserDto(
            id=1,
            user_name="alice",
            first_name="Alice",
            last_name="Smith",
            status=1,
            created_at="2025-10-05T00:00:00Z",
            updated_at="2025-10-05T00:00:00Z",
        ),
        ReadUserDto(
            id=2,
            user_name="bob",
            first_name="Bob",
            last_name="Brown",
            status=1,
            created_at="2025-10-05T00:00:00Z",
            updated_at="2025-10-05T00:00:00Z",
        ),
    ]

    result = user_service.get_all(limit=10, offset=0)

    assert len(result) == 2
    assert all(isinstance(u, ReadUserDto) for u in result)
    mock_user_repository.get_all_users.assert_called_once_with(10, 0)


def test_get_by_id_success(user_service, mock_user_repository):
    """
    Test that `get_by_id()` retrieves a single user successfully.
    """
    mock_user_repository.get_user_by_id.return_value = ReadUserDto(
        id=1,
        user_name="john_doe",
        first_name="John",
        last_name="Doe",
        status=1,
        created_at="2025-10-05T00:00:00Z",
        updated_at="2025-10-05T00:00:00Z",
    )

    result = user_service.get_by_id(1)

    assert isinstance(result, ReadUserDto)
    assert result.user_name == "john_doe"
    mock_user_repository.get_user_by_id.assert_called_once_with(1)


def test_get_by_id_not_found(user_service, mock_user_repository):
    """
    Test that `get_by_id()` raises `UserNotFoundError` when user doesn't exist.
    """
    mock_user_repository.get_user_by_id.side_effect = UserNotFoundError(
        "User not found"
    )

    with pytest.raises(UserNotFoundError):
        user_service.get_by_id(999)


def test_update_user_with_password(user_service, mock_user_repository):
    """
    Test that `update()` hashes password before saving user data.

    Steps:
      1. Prepare an `UpdateUserDto` with plain password.
      2. Mock repository to return updated user.
      3. Assert that password is hashed and plain fields cleared.
    """
    dto = UpdateUserDto(
        user_name="new_name",
        first_name="John",
        last_name="Doe",
        password="StrongPass123!",
        password_confirm="StrongPass123!",
        password_hash=None,
    )

    mock_user_repository.update_user.return_value = ReadUserDto(
        id=1,
        user_name="new_name",
        first_name="John",
        last_name="Doe",
        status=1,
        created_at="2025-10-05T00:00:00Z",
        updated_at="2025-10-05T00:00:00Z",
    )

    result = user_service.update(1, dto)

    assert dto.password is None
    assert dto.password_confirm is None
    assert isinstance(dto.password_hash, bytes)
    assert bcrypt.checkpw(b"StrongPass123!", dto.password_hash)

    assert isinstance(result, ReadUserDto)
    mock_user_repository.update_user.assert_called_once_with(1, dto)


def test_update_user_without_password(user_service, mock_user_repository):
    """
    Test that `update()` does not hash password if none provided.
    """
    dto = UpdateUserDto(
        user_name="johnny",
        first_name="John",
        last_name="Doe",
    )

    mock_user_repository.update_user.return_value = ReadUserDto(
        id=1,
        user_name="johnny",
        first_name="John",
        last_name="Doe",
        status=1,
        created_at="2025-10-05T00:00:00Z",
        updated_at="2025-10-05T00:00:00Z",
    )

    result = user_service.update(1, dto)

    assert dto.password_hash is None
    assert isinstance(result, ReadUserDto)
    mock_user_repository.update_user.assert_called_once_with(1, dto)


def test_update_user_not_found(user_service, mock_user_repository):
    """
    Test that `update()` propagates `UserNotFoundError` if repository fails.
    """
    dto = UpdateUserDto(
        user_name="lost_user",
        first_name="Ghost",
        last_name="Man",
    )

    mock_user_repository.update_user.side_effect = UserNotFoundError("not found")

    with pytest.raises(UserNotFoundError):
        user_service.update(1, dto)


def test_delete_user_success(user_service, mock_user_repository):
    """
    Test that `delete()` calls repository to soft-delete a user successfully.
    """
    user_service.delete(1)
    mock_user_repository.delete_user.assert_called_once_with(1)


def test_delete_user_not_found(user_service, mock_user_repository):
    """
    Test that `delete()` raises `UserNotFoundError` when user doesn't exist.
    """
    mock_user_repository.delete_user.side_effect = UserNotFoundError("not found")

    with pytest.raises(UserNotFoundError):
        user_service.delete(123)
