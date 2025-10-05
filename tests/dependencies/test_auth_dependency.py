from fastapi import status


def test_get_current_user_success(test_app_for_auth_dependencies, valid_token):
    """
    Test successful extraction of a user from a valid JWT access token.

    This test ensures that:
      - A properly signed and structured JWT is successfully decoded.
      - The `get_current_user` dependency correctly returns a `TokenPayload`
        containing the `sub` (user ID) field.
      - The protected route using this dependency returns HTTP 200 with
        the correct user information.

    Steps:
        1. Send a GET request with a valid Bearer token.
        2. Expect status 200 and the decoded user ID in the response.

    Args:
        test_app_for_auth_dependencies (TestClient): FastAPI test client with routes using auth dependencies.
        valid_token (str): A valid JWT access token.

    Raises:
        AssertionError: If the dependency fails to decode the token or returns incorrect user data.
    """
    response = test_app_for_auth_dependencies.get(
        "/protected",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["user_id"] == "42"


def test_get_current_user_missing_header(test_app_for_auth_dependencies):
    """
    Test behavior when the `Authorization` header is missing.

    This test verifies that requests without any `Authorization` header
    are rejected with an HTTP 401 error and the message "Missing token".

    Steps:
        1. Send a GET request without the header.
        2. Expect HTTP 401 and a clear error message.

    Args:
        test_app_for_auth_dependencies (TestClient): FastAPI test client.

    Raises:
        AssertionError: If the route does not return 401 or incorrect error details.
    """
    response = test_app_for_auth_dependencies.get("/protected")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Missing token"


def test_get_current_user_wrong_format(test_app_for_auth_dependencies):
    """
    Test behavior when the `Authorization` header has an invalid format.

    The dependency expects headers of the form:
        Authorization: Bearer <token>
    Any other prefix (e.g., "Token" or "Basic") should result in rejection.

    Steps:
        1. Send a GET request with an invalid header format.
        2. Expect HTTP 401 and the message "Missing token".

    Args:
        test_app_for_auth_dependencies (TestClient): FastAPI test client.

    Raises:
        AssertionError: If the dependency incorrectly accepts malformed headers.
    """
    response = test_app_for_auth_dependencies.get(
        "/protected",
        headers={"Authorization": "Token abcd1234"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Missing token"


def test_get_current_user_invalid_token(test_app_for_auth_dependencies, invalid_token):
    """
    Test rejection of invalid or tampered JWT tokens.

    This test ensures that tokens with invalid signatures, incorrect encoding,
    or malformed payloads are rejected with HTTP 401 and an "Invalid token" message.

    Steps:
        1. Send a GET request with a syntactically invalid token.
        2. Expect HTTP 401 and a descriptive error response.

    Args:
        test_app_for_auth_dependencies (TestClient): FastAPI test client.
        invalid_token (str): A deliberately invalid JWT token (wrong signature or format).

    Raises:
        AssertionError: If invalid tokens are accepted or an incorrect error code is returned.
    """
    response = test_app_for_auth_dependencies.get(
        "/protected",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid token"
