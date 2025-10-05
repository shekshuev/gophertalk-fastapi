from fastapi import status

from gophertalk_fastapi.models.auth import ReadTokenDto
from gophertalk_fastapi.service.auth_service import WrongPasswordError


def test_login_success(test_client, mock_auth_service):
    """
    Test successful login endpoint behavior.

    Steps:
      1. Mock AuthService.login to return a ReadTokenDto.
      2. Send POST /auth/login with valid credentials.
      3. Assert response status 200 and returned tokens.
    """
    mock_auth_service.login.return_value = ReadTokenDto(
        access_token="access123", refresh_token="refresh123"
    )

    payload = {"user_name": "john_doe", "password": "Secret123!"}
    response = test_client.post("/auth/login", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["access_token"] == "access123"
    assert data["refresh_token"] == "refresh123"
    mock_auth_service.login.assert_called_once()


def test_login_wrong_password(test_client, mock_auth_service):
    """
    Test that login endpoint returns 401 when WrongPasswordError is raised.
    """
    mock_auth_service.login.side_effect = WrongPasswordError("Wrong password")

    payload = {"user_name": "john_doe", "password": "Wrong123!"}
    response = test_client.post("/auth/login", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Wrong password" in response.text


def test_login_unexpected_error(test_client, mock_auth_service):
    """
    Test that login endpoint returns 400 when an unexpected exception occurs.
    """
    mock_auth_service.login.side_effect = ValueError("Unexpected error")

    payload = {"user_name": "john_doe", "password": "Secret123!"}
    response = test_client.post("/auth/login", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unexpected error" in response.text


def test_register_success(test_client, mock_auth_service):
    """
    Test successful registration endpoint behavior.

    Steps:
      1. Mock AuthService.register to return ReadTokenDto.
      2. Send POST /auth/register with valid user data.
      3. Assert response status 201 and returned tokens.
    """
    mock_auth_service.register.return_value = ReadTokenDto(
        access_token="access123", refresh_token="refresh123"
    )

    payload = {
        "user_name": "new_user",
        "first_name": "John",
        "last_name": "Doe",
        "password": "StrongP@ss1",
        "password_confirm": "StrongP@ss1",
    }

    response = test_client.post("/auth/register", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["access_token"] == "access123"
    assert data["refresh_token"] == "refresh123"
    mock_auth_service.register.assert_called_once()


def test_register_error(test_client, mock_auth_service):
    """
    Test that registration endpoint returns 400 on service-layer exception.
    """
    mock_auth_service.register.side_effect = Exception("Username already exists")

    payload = {
        "user_name": "existing_user",
        "first_name": "Alice",
        "last_name": "Smith",
        "password": "StrongP@ss1",
        "password_confirm": "StrongP@ss1",
    }

    response = test_client.post("/auth/register", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username already exists" in response.text
