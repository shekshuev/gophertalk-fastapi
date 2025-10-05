import bcrypt
import pytest
from jose import jwt

from gophertalk_fastapi.models.auth import LoginUserDto, ReadTokenDto, RegisterUserDto
from gophertalk_fastapi.models.user import CreateUserDto, ReadAuthUserDataDto
from gophertalk_fastapi.repository.user_repository import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from gophertalk_fastapi.service.auth_service import WrongPasswordError


def test_login_success(auth_service, mock_user_repository, mock_config):
    """
    Test that `login()` authenticates a user successfully and returns JWT tokens.

    Steps:
      1. Mock `get_user_by_username()` to return a valid user with a bcrypt hash.
      2. Mock `bcrypt.checkpw` to return True.
      3. Call `login()` with valid credentials.
      4. Assert that JWT tokens are returned and properly decodable.
    """
    password = "Qwerty123!"
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    mock_user_repository.get_user_by_username.return_value = ReadAuthUserDataDto(
        id=1, user_name="john_doe", password_hash=password_hash, status=1
    )

    dto = LoginUserDto(user_name="john_doe", password=password)
    result = auth_service.login(dto)

    assert isinstance(result, ReadTokenDto)
    decoded_access = jwt.decode(
        result.access_token, mock_config.access_token_secret, algorithms=["HS256"]
    )
    decoded_refresh = jwt.decode(
        result.refresh_token, mock_config.refresh_token_secret, algorithms=["HS256"]
    )

    assert decoded_access["sub"] == "1"
    assert decoded_refresh["sub"] == "1"
    mock_user_repository.get_user_by_username.assert_called_once_with("john_doe")


def test_login_wrong_password(auth_service, mock_user_repository):
    """
    Test that `login()` raises `WrongPasswordError` when the password does not match.
    """
    password_hash = bcrypt.hashpw(b"Qwerty123!", bcrypt.gensalt()).decode()
    mock_user_repository.get_user_by_username.return_value = ReadAuthUserDataDto(
        id=1, user_name="john_doe", password_hash=password_hash, status=1
    )

    dto = LoginUserDto(user_name="john_doe", password="Qwerty321!")

    with pytest.raises(WrongPasswordError):
        auth_service.login(dto)


def test_login_user_not_found(auth_service, mock_user_repository):
    """
    Test that `login()` propagates `UserNotFoundError` when username does not exist.
    """
    mock_user_repository.get_user_by_username.side_effect = UserNotFoundError(
        "not found"
    )

    dto = LoginUserDto(user_name="ghost", password="Qwerty123!")

    with pytest.raises(UserNotFoundError):
        auth_service.login(dto)


def test_register_success(auth_service, mock_user_repository):
    """
    Test that `register()` creates a new user and returns valid JWT tokens.

    Steps:
      1. Mock `create_user()` to return a user DTO with an ID.
      2. Ensure bcrypt.hashpw is called correctly.
      3. Assert JWT tokens are valid and associated with the user ID.
    """
    mock_user_repository.create_user.return_value = ReadAuthUserDataDto(
        id=42, user_name="new_user", password_hash="hashed_pw", status=1
    )

    dto = RegisterUserDto(
        user_name="new_user",
        first_name="John",
        last_name="Doe",
        password="StrongP@ss1",
        password_confirm="StrongP@ss1",
    )

    result = auth_service.register(dto)

    assert isinstance(result, ReadTokenDto)
    decoded_access = jwt.decode(
        result.access_token, auth_service.cfg.access_token_secret, algorithms=["HS256"]
    )
    assert decoded_access["sub"] == "42"

    mock_user_repository.create_user.assert_called_once()
    created_user_arg = mock_user_repository.create_user.call_args[0][0]
    assert isinstance(created_user_arg, CreateUserDto)
    assert created_user_arg.user_name == "new_user"
    assert created_user_arg.password_hash != dto.password


def test_register_user_already_exists(auth_service, mock_user_repository):
    """
    Test that `register()` raises `UserAlreadyExistsError` when username is taken.
    """
    mock_user_repository.create_user.side_effect = UserAlreadyExistsError("exists")

    dto = RegisterUserDto(
        user_name="taken_user",
        first_name="Alice",
        last_name="Smith",
        password="StrongP@ss1",
        password_confirm="StrongP@ss1",
    )

    with pytest.raises(UserAlreadyExistsError):
        auth_service.register(dto)


def test_generate_token_pair_valid(auth_service, mock_config):
    """
    Test that `generate_token_pair()` creates valid JWT tokens with correct claims.
    """
    result = auth_service.generate_token_pair(user_id=99)
    assert isinstance(result, ReadTokenDto)

    decoded_access = jwt.decode(
        result.access_token, mock_config.access_token_secret, algorithms=["HS256"]
    )
    decoded_refresh = jwt.decode(
        result.refresh_token, mock_config.refresh_token_secret, algorithms=["HS256"]
    )

    assert decoded_access["sub"] == "99"
    assert decoded_refresh["sub"] == "99"
    assert "exp" in decoded_access
    assert "exp" in decoded_refresh
