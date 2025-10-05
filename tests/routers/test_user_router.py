from fastapi import status

from gophertalk_fastapi.models.user import ReadUserDto, UpdateUserDto
from gophertalk_fastapi.repository.user_repository import UserNotFoundError


def test_get_all_users_success(test_client, mock_user_service):
    """Test successful retrieval of all users."""
    mock_user_service.get_all.return_value = [
        ReadUserDto(
            id=1,
            user_name="john",
            first_name="John",
            last_name="Doe",
            status=1,
            created_at="2025-10-05T00:00:00Z",
            updated_at="2025-10-05T00:00:00Z",
        )
    ]

    response = test_client.get("/users?limit=5&offset=0")

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert response.json()[0]["user_name"] == "john"
    mock_user_service.get_all.assert_called_once_with(5, 0)


def test_get_all_users_failure(test_client, mock_user_service):
    """Test that an exception in the service raises HTTP 400."""
    mock_user_service.get_all.side_effect = Exception("Unexpected error")

    response = test_client.get("/users")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unexpected error" in response.json()["detail"]


def test_get_user_by_id_success(test_client, mock_user_service):
    """Test successful retrieval of a user by ID."""
    mock_user_service.get_by_id.return_value = ReadUserDto(
        id=1,
        user_name="jane",
        first_name="Jane",
        last_name="Smith",
        status=1,
        created_at="2025-10-05T00:00:00Z",
        updated_at="2025-10-05T00:00:00Z",
    )

    response = test_client.get("/users/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["user_name"] == "jane"
    mock_user_service.get_by_id.assert_called_once_with(1)


def test_get_user_by_id_not_found(test_client, mock_user_service):
    """Test that UserNotFoundError triggers 404 response."""
    mock_user_service.get_by_id.side_effect = UserNotFoundError("User not found")

    response = test_client.get("/users/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


def test_update_user_success(test_client, mock_user_service):
    """Test successful update of a user."""
    dto = UpdateUserDto(first_name="Jack", last_name="White", user_name="jackwhite")
    updated_user = ReadUserDto(
        id=1,
        user_name="jackwhite",
        first_name="Jack",
        last_name="White",
        status=1,
        created_at="2025-10-05T00:00:00Z",
        updated_at="2025-10-05T00:00:00Z",
    )

    mock_user_service.update.return_value = updated_user

    response = test_client.put("/users/1", json=dto.__dict__)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["user_name"] == "jackwhite"
    mock_user_service.update.assert_called_once()


def test_update_user_not_found(test_client, mock_user_service):
    """Test update of a non-existing user returns 404."""
    mock_user_service.update.side_effect = UserNotFoundError("User not found")

    response = test_client.put("/users/999", json={"first_name": "Nope"})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "User not found" in response.json()["detail"]


def test_update_user_generic_error(test_client, mock_user_service):
    """Test that unexpected errors return 400."""
    mock_user_service.update.side_effect = Exception("Database exploded")

    response = test_client.put("/users/1", json={"first_name": "Fail"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Database exploded" in response.json()["detail"]


def test_delete_user_success(test_client, mock_user_service):
    """Test successful deletion of a user."""
    response = test_client.delete("/users/1")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_user_service.delete.assert_called_once_with(1)


def test_delete_user_not_found(test_client, mock_user_service):
    """Test that deleting a non-existent user returns 404."""
    mock_user_service.delete.side_effect = UserNotFoundError("User not found")

    response = test_client.delete("/users/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


def test_delete_user_generic_error(test_client, mock_user_service):
    """Test that unexpected errors return 400."""
    mock_user_service.delete.side_effect = Exception("Unexpected failure")

    response = test_client.delete("/users/1")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unexpected failure" in response.json()["detail"]
