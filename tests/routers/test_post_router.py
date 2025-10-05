from datetime import UTC, datetime

from fastapi import status

from gophertalk_fastapi.models.post import ReadPostDto, ReadPostUserDto


def test_get_all_posts_success(test_client, mock_post_service, valid_token):
    """
    Test successful retrieval of posts with valid filters and authentication.

    This test verifies that:
      - The `/posts` endpoint correctly invokes the service layer with a `FilterPostDto`.
      - Returns a valid list of `ReadPostDto` objects.
      - Responds with HTTP 200 when executed with a valid JWT token.

    Steps:
        1. Mock the service's `get_all_posts` method to return a sample post.
        2. Perform a GET request with Bearer token and query params.
        3. Assert correct response format and HTTP status.

    Raises:
        AssertionError: If the endpoint fails to return 200 or returns unexpected data.
    """
    mock_post_service.get_all_posts.return_value = [
        ReadPostDto(
            id=1,
            text="Hello world!",
            user_id=1,
            reply_to_id=None,
            created_at=datetime.now(UTC),
            likes_count=5,
            views_count=2,
            user=ReadPostUserDto(
                id=1, user_name="john", first_name="John", last_name="Doe"
            ),
        )
    ]

    response = test_client.get(
        "/posts?limit=5&offset=0",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["text"] == "Hello world!"
    mock_post_service.get_all_posts.assert_called_once()


def test_get_all_posts_failure(test_client, mock_post_service, valid_token):
    """
    Test that `/posts` returns 400 when the service raises an exception.

    This ensures that unhandled internal errors are translated into
    standardized HTTP exceptions with appropriate status codes.
    """
    mock_post_service.get_all_posts.side_effect = Exception("Database error")

    response = test_client.get(
        "/posts",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Database error" in response.json()["detail"]


def test_create_post_success(test_client, mock_post_service, valid_token):
    """
    Test successful post creation with valid input and authentication.

    Verifies:
      - The `create_post` method of the service is called with correct DTO.
      - Endpoint returns 201 and a properly structured post response.
    """
    created_post = ReadPostDto(
        id=1,
        text="My first post",
        user_id=42,
        reply_to_id=None,
        created_at=datetime.now(UTC),
        likes_count=0,
        views_count=0,
        user=ReadPostUserDto(
            id=42, user_name="tester", first_name="Jack", last_name="White"
        ),
    )
    mock_post_service.create_post.return_value = created_post

    response = test_client.post(
        "/posts",
        json={"text": "My first post"},
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["text"] == "My first post"
    mock_post_service.create_post.assert_called_once()


def test_create_post_failure(test_client, mock_post_service, valid_token):
    """Test that `/posts` returns 400 when post creation fails."""
    mock_post_service.create_post.side_effect = Exception("Insert failed")

    response = test_client.post(
        "/posts",
        json={"text": "Invalid post"},
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Insert failed" in response.json()["detail"]


def test_delete_post_success(test_client, mock_post_service, valid_token):
    """
    Test successful soft deletion of a post.

    Ensures that the route returns HTTP 204 and calls service correctly.
    """
    response = test_client.delete(
        "/posts/1",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_post_service.delete_post.assert_called_once_with(1, "42")


def test_delete_post_not_found(test_client, mock_post_service, valid_token):
    """Test that deleting a non-existent post returns 404."""
    mock_post_service.delete_post.side_effect = Exception("Post not found")

    response = test_client.delete(
        "/posts/999",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Post not found" in response.json()["detail"]


def test_view_post_success(test_client, mock_post_service, valid_token):
    """Test marking a post as viewed successfully."""
    response = test_client.post(
        "/posts/1/view",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    mock_post_service.view_post.assert_called_once_with(1, "42")


def test_view_post_not_found(test_client, mock_post_service, valid_token):
    """Test that viewing a non-existent post returns 404."""
    mock_post_service.view_post.side_effect = Exception("Post not found")

    response = test_client.post(
        "/posts/999/view",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Post not found" in response.json()["detail"]


def test_like_post_success(test_client, mock_post_service, valid_token):
    """Test successful liking of a post."""
    response = test_client.post(
        "/posts/1/like",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    mock_post_service.like_post.assert_called_once_with(1, "42")


def test_like_post_failure(test_client, mock_post_service, valid_token):
    """Test that liking a post fails with 404 when service raises."""
    mock_post_service.like_post.side_effect = Exception("Already liked")

    response = test_client.post(
        "/posts/1/like",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Already liked" in response.json()["detail"]


def test_dislike_post_success(test_client, mock_post_service, valid_token):
    """Test successful unliking (dislike) of a post."""
    response = test_client.delete(
        "/posts/1/like",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_post_service.dislike_post.assert_called_once_with(1, "42")


def test_dislike_post_not_found(test_client, mock_post_service, valid_token):
    """Test that unliking a non-existent post returns 404."""
    mock_post_service.dislike_post.side_effect = Exception("Post not found")

    response = test_client.delete(
        "/posts/999/like",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Post not found" in response.json()["detail"]
