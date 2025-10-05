from unittest.mock import MagicMock

import pytest

from gophertalk_fastapi.config.config import Config
from gophertalk_fastapi.repository.post_repository import PostRepository
from gophertalk_fastapi.repository.user_repository import UserRepository
from gophertalk_fastapi.service.auth_service import AuthService
from gophertalk_fastapi.service.user_service import UserService


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
def mock_config():
    """
    Provide a mock configuration object for testing.

    This fixture supplies a `Config` instance with dummy but valid settings
    for database connection and JWT token generation, allowing services
    and repositories to operate without external dependencies.

    Returns:
        Config: A mock configuration object with test-safe parameters.
    """
    return Config(
        database_host="test",
        database_port=5432,
        database_name="test",
        database_user="test",
        database_password="test",
        access_token_secret="access_secret",
        refresh_token_secret="refresh_secret",
        access_token_expires=60,
        refresh_token_expires=3600,
    )


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


@pytest.fixture
def mock_user_repository():
    """
    Provide a fully mocked UserRepository for service-layer testing.

    This fixture defines a mock repository with its core methods
    (`get_user_by_username`, `create_user`) pre-initialized as MagicMock objects,
    allowing precise control over repository behavior during AuthService tests.

    Returns:
        MagicMock: Mocked user repository.
    """
    mock_repo = MagicMock()
    mock_repo.get_user_by_username = MagicMock()
    mock_repo.create_user = MagicMock()
    return mock_repo


@pytest.fixture
def auth_service(mock_user_repository, mock_config):
    """
    Provide an AuthService instance configured for isolated unit testing.

    This fixture injects a mocked user repository and a mock configuration
    to test authentication and token generation logic without requiring
    a database or external services.

    Args:
        mock_user_repository (MagicMock): Mocked UserRepository.
        mock_config (Config): Mock configuration with JWT secrets and expirations.

    Returns:
        AuthService: Service instance ready for testing.
    """
    return AuthService(user_repository=mock_user_repository, cfg=mock_config)


@pytest.fixture
def user_service(mock_user_repository, mock_config):
    """
    Provide a UserService instance configured for isolated unit testing.

    This fixture creates a `UserService` using mocked dependencies to
    ensure the service logic (password hashing, user update, retrieval,
    and deletion) can be tested independently of a real database or external
    configuration.

    Args:
        mock_user_repository (MagicMock): Mocked UserRepository for database interaction.
        mock_config (Config): Mock configuration with application settings.

    Returns:
        UserService: A fully initialized service instance ready for testing.
    """
    return UserService(user_repository=mock_user_repository, cfg=mock_config)
