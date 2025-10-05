import pytest

from gophertalk_fastapi.models.post import CreatePostDto, FilterPostDto
from gophertalk_fastapi.repository.post_repository import (
    PostAlreadyLikedError,
    PostAlreadyViewedError,
    PostNotFoundError,
    PostRepositoryError,
    ReplyToPostDoesNotExistsError,
)


def test_get_all_posts_success(post_service, mock_post_repository):
    """
    Test that `get_all_posts()` delegates correctly to the repository.

    Steps:
      1. Mock repository's `get_all_posts` to return a list of posts.
      2. Call the service method with a valid FilterPostDto.
      3. Assert that the same list is returned.
      4. Verify the repository call.
    """
    expected_result = ["post1", "post2"]
    mock_post_repository.get_all_posts.return_value = expected_result

    dto = FilterPostDto(limit=10, offset=0)
    result = post_service.get_all_posts(dto)

    assert result == expected_result
    mock_post_repository.get_all_posts.assert_called_once_with(dto)


def test_get_all_posts_error(post_service, mock_post_repository):
    """
    Test that `get_all_posts()` propagates repository-level errors.
    """
    mock_post_repository.get_all_posts.side_effect = PostRepositoryError("DB failed")

    dto = FilterPostDto(limit=10, offset=0)
    with pytest.raises(PostRepositoryError):
        post_service.get_all_posts(dto)


def test_create_post_success(post_service, mock_post_repository):
    """
    Test that `create_post()` successfully delegates to repository and returns result.
    """
    expected_post = {"id": 1, "text": "Hello", "user_id": 5}
    mock_post_repository.create_post.return_value = expected_post

    dto = CreatePostDto(text="Hello", user_id=5, reply_to_id=None)
    result = post_service.create_post(dto)

    assert result == expected_post
    mock_post_repository.create_post.assert_called_once_with(dto)


def test_create_post_reply_to_not_exists(post_service, mock_post_repository):
    """
    Test that `create_post()` raises `ReplyToPostDoesNotExistsError` if reply target is missing.
    """
    mock_post_repository.create_post.side_effect = ReplyToPostDoesNotExistsError(
        "missing"
    )

    dto = CreatePostDto(text="Reply", user_id=1, reply_to_id=999)
    with pytest.raises(ReplyToPostDoesNotExistsError):
        post_service.create_post(dto)


def test_create_post_repository_error(post_service, mock_post_repository):
    """
    Test that `create_post()` raises `PostRepositoryError` for unexpected DB errors.
    """
    mock_post_repository.create_post.side_effect = PostRepositoryError("Unknown error")

    dto = CreatePostDto(text="Something", user_id=1, reply_to_id=None)
    with pytest.raises(PostRepositoryError):
        post_service.create_post(dto)


def test_delete_post_success(post_service, mock_post_repository):
    """
    Test that `delete_post()` delegates to repository correctly.
    """
    post_service.delete_post(1, 42)
    mock_post_repository.delete_post.assert_called_once_with(1, 42)


def test_delete_post_not_found(post_service, mock_post_repository):
    """
    Test that `delete_post()` raises `PostNotFoundError` when post doesn't exist.
    """
    mock_post_repository.delete_post.side_effect = PostNotFoundError("Not found")
    with pytest.raises(PostNotFoundError):
        post_service.delete_post(1, 42)


def test_view_post_success(post_service, mock_post_repository):
    """
    Test that `view_post()` calls the repository method correctly.
    """
    post_service.view_post(1, 2)
    mock_post_repository.view_post.assert_called_once_with(1, 2)


def test_view_post_already_viewed(post_service, mock_post_repository):
    """
    Test that `view_post()` raises `PostAlreadyViewedError` when user already viewed the post.
    """
    mock_post_repository.view_post.side_effect = PostAlreadyViewedError(
        "Already viewed"
    )
    with pytest.raises(PostAlreadyViewedError):
        post_service.view_post(1, 2)


def test_like_post_success(post_service, mock_post_repository):
    """
    Test that `like_post()` delegates correctly to the repository.
    """
    post_service.like_post(5, 10)
    mock_post_repository.like_post.assert_called_once_with(5, 10)


def test_like_post_already_liked(post_service, mock_post_repository):
    """
    Test that `like_post()` raises `PostAlreadyLikedError` when the user already liked it.
    """
    mock_post_repository.like_post.side_effect = PostAlreadyLikedError("Already liked")
    with pytest.raises(PostAlreadyLikedError):
        post_service.like_post(5, 10)


def test_dislike_post_success(post_service, mock_post_repository):
    """
    Test that `dislike_post()` delegates correctly to the repository.
    """
    post_service.dislike_post(5, 10)
    mock_post_repository.dislike_post.assert_called_once_with(5, 10)


def test_dislike_post_error(post_service, mock_post_repository):
    """
    Test that `dislike_post()` raises `PostRepositoryError` on unexpected DB error.
    """
    mock_post_repository.dislike_post.side_effect = PostRepositoryError("DB fail")
    with pytest.raises(PostRepositoryError):
        post_service.dislike_post(5, 10)
