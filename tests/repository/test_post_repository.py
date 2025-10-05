import re
from datetime import datetime

import psycopg
import pytest

from gophertalk_fastapi.models.post import (
    CreatePostDto,
    FilterPostDto,
    ReadPostDto,
)
from gophertalk_fastapi.repository.post_repository import (
    PostAlreadyLikedError,
    PostAlreadyViewedError,
    PostNotFoundError,
    PostRepositoryError,
    ReplyToPostDoesNotExistsError,
)


def test_create_post_success(post_repository, mock_pool):
    """
    Test that `create_post()` successfully inserts a new post into the database.

    This test verifies:
      - The repository executes the correct INSERT query.
      - The returned object is an instance of `ReadPostDto`.
      - The correct parameters are passed to the SQL query.

    Steps:
      1. Mock `fetchone()` to return a valid post row with all required fields.
      2. Call `create_post()` with valid input data.
      3. Assert the returned DTO has correct attributes.
      4. Validate the SQL query and parameters.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.fetchone.return_value = {
        "id": 1,
        "text": "Hello world!",
        "user_id": 5,
        "reply_to_id": None,
        "created_at": datetime.now(),
    }

    dto = CreatePostDto(text="Hello world!", user_id=5, reply_to_id=None)
    result = post_repository.create_post(dto)

    assert isinstance(result, ReadPostDto)
    assert result.text == "Hello world!"
    assert result.user_id == 5

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]

    assert re.search(
        r"insert\s+into\s+posts.*\(.*(?=.*text.*)(?=.*reply_to_id.*)(?=.*user_id.*).*\)",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert re.search(
        r"returning.*(?=.*id.*)(?=.*text.*)(?=.*reply_to_id.*)(?=.*user_id.*)(?=.*created_at.*).*",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert params == ("Hello world!", 5, None)


def test_create_post_reply_to_not_exists(post_repository, mock_pool):
    """
    Test that `create_post()` raises `ReplyToPostDoesNotExistsError`
    when the referenced reply_to_id does not exist.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.ForeignKeyViolation(
        "invalid reply_to_id"
    )

    dto = CreatePostDto(text="Replying", user_id=1, reply_to_id=999)

    with pytest.raises(ReplyToPostDoesNotExistsError):
        post_repository.create_post(dto)


def test_create_post_unknown_error(post_repository, mock_pool):
    """
    Test that `create_post()` raises `PostRepositoryError`
    for unexpected database errors.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.Error("unexpected failure")

    dto = CreatePostDto(text="Some text", user_id=2, reply_to_id=None)

    with pytest.raises(PostRepositoryError):
        post_repository.create_post(dto)


def test_get_all_posts_success(post_repository, mock_pool):
    """
    Test that `get_all_posts()` successfully retrieves posts with filters and pagination.

    This test verifies:
      - The repository executes the expected SQL query with correct JOINs and WHERE conditions.
      - The returned list consists of `ReadPostDto` objects.
      - The SQL parameters match the provided filter DTO.

    Steps:
      1. Mock `fetchall()` to return valid post rows.
      2. Call `get_all_posts()` with a populated `FilterPostDto`.
      3. Validate returned data and SQL structure.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.fetchall.return_value = [
        {
            "id": 1,
            "text": "First post",
            "reply_to_id": None,
            "created_at": datetime.now(),
            "user_id": 1,
            "user_name": "john",
            "first_name": "John",
            "last_name": "Doe",
            "likes_count": 10,
            "views_count": 5,
            "replies_count": 2,
            "user_liked": True,
            "user_viewed": True,
        },
        {
            "id": 2,
            "text": "Second post",
            "reply_to_id": None,
            "created_at": datetime.now(),
            "user_id": 2,
            "user_name": "jane",
            "first_name": "Jane",
            "last_name": "Smith",
            "likes_count": 3,
            "views_count": 1,
            "replies_count": 0,
            "user_liked": False,
            "user_viewed": False,
        },
    ]

    dto = FilterPostDto(
        search="post",
        owner_id=1,
        user_id=10,
        reply_to_id=None,
        limit=10,
        offset=0,
    )

    result = post_repository.get_all_posts(dto)

    assert isinstance(result, list)
    assert all(isinstance(p, ReadPostDto) for p in result)
    assert result[0].text == "First post"

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]

    assert re.search(
        r"select.*from\s+posts.*",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert re.search(
        r"where.*deleted_at\s+is\s+null",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert re.search(
        r"order\s+by\s+p\.created_at\s+desc",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )

    assert params[:2] == [dto.user_id, dto.user_id]
    assert "%post%" in params
    assert dto.owner_id in params
    assert dto.limit in params
    assert dto.offset in params


def test_get_all_posts_with_reply_to(post_repository, mock_pool):
    """
    Test that `get_all_posts()` adds correct ORDER BY ASC clause when filtering by `reply_to_id`.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.fetchall.return_value = []

    dto = FilterPostDto(
        search=None,
        owner_id=None,
        user_id=7,
        reply_to_id=3,
        limit=5,
        offset=0,
    )

    post_repository.get_all_posts(dto)

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]

    assert re.search(
        r"order\s+by\s+p\.created_at\s+asc",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert dto.reply_to_id in params


def test_get_all_posts_unknown_error(post_repository, mock_pool):
    """
    Test that `get_all_posts()` raises `PostRepositoryError` for unexpected database errors.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.Error("unexpected failure")

    dto = FilterPostDto(user_id=1, limit=10, offset=0)

    with pytest.raises(PostRepositoryError):
        post_repository.get_all_posts(dto)


def test_get_post_by_id_success(post_repository, mock_pool):
    """
    Test that `get_post_by_id()` successfully retrieves a post by its ID.

    This test verifies:
      - The repository executes the expected SQL SELECT query.
      - The returned object is a valid instance of `ReadPostDto`.
      - The correct parameters (user_id x2 + post_id) are passed.

    Steps:
      1. Mock `fetchone()` to return a valid post row.
      2. Call `get_post_by_id()` with test post_id and user_id.
      3. Assert correct DTO mapping and SQL structure.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.fetchone.return_value = {
        "post_id": 1,
        "text": "Hello world!",
        "reply_to_id": None,
        "created_at": "2025-10-05T00:00:00Z",
        "user_id": 2,
        "user_name": "john_doe",
        "first_name": "John",
        "last_name": "Doe",
        "likes_count": 3,
        "views_count": 5,
        "replies_count": 1,
        "user_liked": True,
        "user_viewed": False,
    }

    post_id = 1
    user_id = 10

    result = post_repository.get_post_by_id(post_id=post_id, user_id=user_id)

    assert isinstance(result, ReadPostDto)
    assert result.text == "Hello world!"
    assert result.user_id == 2

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]

    assert re.search(
        r"select\s+.*from\s+posts.*",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert re.search(
        r"where\s+(?=.*deleted_at\s+is\s+null.*)(?=.*id\s*=\s*%s.*)",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )

    assert params == (user_id, user_id, post_id)


def test_get_post_by_id_not_found(post_repository, mock_pool):
    """
    Test that `get_post_by_id()` raises `PostNotFoundError`
    when no post exists with the given ID.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.fetchone.return_value = None

    with pytest.raises(PostNotFoundError):
        post_repository.get_post_by_id(post_id=999, user_id=1)


def test_get_post_by_id_unknown_error(post_repository, mock_pool):
    """
    Test that `get_post_by_id()` raises `PostRepositoryError`
    when an unexpected database error occurs.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.Error("unexpected failure")

    with pytest.raises(PostRepositoryError):
        post_repository.get_post_by_id(post_id=1, user_id=1)


def test_delete_post_success(post_repository, mock_pool):
    """
    Test that `delete_post()` successfully soft-deletes a post.

    This test verifies:
      - The repository executes the expected UPDATE query.
      - The correct SQL parameters (post_id, owner_id) are passed.
      - `PostNotFoundError` is not raised when `rowcount > 0`.

    Steps:
      1. Mock the cursor's `rowcount` to simulate successful update.
      2. Call `delete_post()` with valid `post_id` and `owner_id`.
      3. Verify SQL structure and parameter correctness.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.rowcount = 1

    post_id = 42
    owner_id = 7
    post_repository.delete_post(post_id=post_id, owner_id=owner_id)

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]

    assert re.search(
        r"update\s+posts\s+set\s+deleted_at\s*=\s*now\(\)",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert re.search(
        r"where\s+(?=.*id\s*=\s*%s.*)(?=.*user_id\s*=\s*%s.*)(?=.*deleted_at\s+is\s+null.*)",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )

    assert params == (post_id, owner_id)


def test_delete_post_not_found(post_repository, mock_pool):
    """
    Test that `delete_post()` raises `PostNotFoundError`
    when no matching post is found or already deleted.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.rowcount = 0

    post_id = 123
    owner_id = 10

    with pytest.raises(PostNotFoundError):
        post_repository.delete_post(post_id=post_id, owner_id=owner_id)


def test_delete_post_unknown_error(post_repository, mock_pool):
    """
    Test that `delete_post()` raises `PostRepositoryError`
    for unexpected database exceptions.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.Error("unexpected failure")

    with pytest.raises(PostRepositoryError):
        post_repository.delete_post(post_id=1, owner_id=1)


def test_view_post_success(post_repository, mock_pool):
    """
    Test that `view_post()` inserts a new view record successfully.

    Verifies:
      - The expected INSERT SQL query is executed.
      - Correct parameters (post_id, user_id) are passed.
      - No exceptions are raised when insertion succeeds.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.rowcount = 1
    post_repository.view_post(post_id=10, user_id=5)

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]

    assert re.search(
        r"insert\s+into\s+views.*\(.*(?=.*user_id.*)(?=.*post_id.*).*\).*values",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert params == (10, 5)


def test_view_post_foreign_key_violation(post_repository, mock_pool):
    """
    Test that `view_post()` raises `PostRepositoryError`
    when the post or user does not exist.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.ForeignKeyViolation("invalid FK")

    with pytest.raises(PostRepositoryError, match="User or post not found"):
        post_repository.view_post(post_id=99, user_id=1)


def test_view_post_unique_violation(post_repository, mock_pool):
    """
    Test that `view_post()` raises `PostAlreadyViewedError`
    when a user tries to view the same post twice.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.UniqueViolation("pk__views")

    with pytest.raises(PostAlreadyViewedError):
        post_repository.view_post(post_id=10, user_id=5)


def test_view_post_unknown_error(post_repository, mock_pool):
    """
    Test that `view_post()` raises `PostRepositoryError` for unexpected DB errors.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.Error("unexpected")

    with pytest.raises(PostRepositoryError):
        post_repository.view_post(post_id=10, user_id=5)


def test_like_post_success(post_repository, mock_pool):
    """
    Test that `like_post()` successfully inserts a new like record.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.rowcount = 1
    post_repository.like_post(post_id=1, user_id=2)

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]

    assert re.search(
        r"insert\s+into\s+likes.*\(.*(?=.*user_id.*)(?=.*post_id.*).*\).*values",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert params == (1, 2)


def test_like_post_foreign_key_violation(post_repository, mock_pool):
    """
    Test that `like_post()` raises `PostRepositoryError`
    if post or user does not exist.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.ForeignKeyViolation("invalid FK")

    with pytest.raises(PostRepositoryError, match="User or post not found"):
        post_repository.like_post(post_id=1, user_id=99)


def test_like_post_unique_violation(post_repository, mock_pool):
    """
    Test that `like_post()` raises `PostAlreadyLikedError`
    when the user already liked the post.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.UniqueViolation("pk__likes")

    with pytest.raises(PostAlreadyLikedError):
        post_repository.like_post(post_id=1, user_id=1)


def test_like_post_unknown_error(post_repository, mock_pool):
    """
    Test that `like_post()` raises `PostRepositoryError` for unexpected DB errors.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.Error("unexpected")

    with pytest.raises(PostRepositoryError):
        post_repository.like_post(post_id=1, user_id=1)


def test_dislike_post_success(post_repository, mock_pool):
    """
    Test that `dislike_post()` deletes a like record successfully.

    Verifies:
      - DELETE FROM likes query is executed.
      - Parameters (post_id, user_id) are correct.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.rowcount = 1
    post_repository.dislike_post(post_id=10, user_id=3)

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]

    assert re.search(
        r"delete\s+from\s+likes\s+where.*(?=.*user_id\s*=\s*%s)(?=.*post_id\s*=\s*%s.*).*",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert params == (10, 3)


def test_dislike_post_unknown_error(post_repository, mock_pool):
    """
    Test that `dislike_post()` raises `PostRepositoryError`
    when the database operation fails unexpectedly.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.Error("unexpected failure")

    with pytest.raises(PostRepositoryError):
        post_repository.dislike_post(post_id=1, user_id=1)
