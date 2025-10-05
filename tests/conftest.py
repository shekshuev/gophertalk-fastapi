from unittest.mock import MagicMock

import pytest

from gophertalk_fastapi.repository.post_repository import PostRepository
from gophertalk_fastapi.repository.user_repository import UserRepository


@pytest.fixture
def mock_pool():
    """
    Create a fully mocked ConnectionPool object for repository testing.

    This fixture mocks the entire connection chain used by psycopg_pool:
        pool.connection() → context manager (__enter__) → connection
        connection.cursor() → context manager (__enter__) → cursor

    Returns:
        MagicMock: A mocked connection pool that simulates
        database behavior without requiring a real PostgreSQL instance.
    """
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_pool = MagicMock()

    mock_pool.connection.return_value.__enter__.return_value = mock_conn

    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    return mock_pool


@pytest.fixture
def user_repository(mock_pool):
    """
    Provide a UserRepository instance with a mocked ConnectionPool.

    This fixture allows testing repository methods in isolation
    by injecting a mocked connection pool instead of a real database.

    Args:
        mock_pool (MagicMock): The mocked database connection pool.

    Returns:
        UserRepository: Repository instance configured with the mock pool.
    """
    return UserRepository(pool=mock_pool)


@pytest.fixture
def post_repository(mock_pool):
    """
    Provide a PostRepository instance with a mocked ConnectionPool.

    This fixture allows testing repository methods in isolation
    by injecting a mocked connection pool instead of a real database.

    Args:
        mock_pool (MagicMock): The mocked database connection pool.

    Returns:
        UserRepository: Repository instance configured with the mock pool.
    """
    return PostRepository(pool=mock_pool)
