from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from gophertalk_fastapi.config.config import Config
from gophertalk_fastapi.repository.post_repository import PostRepository
from gophertalk_fastapi.repository.user_repository import UserRepository
from gophertalk_fastapi.routers.auth_router import AuthRouter
from gophertalk_fastapi.routers.user_router import UserRouter
from gophertalk_fastapi.service.auth_service import AuthService
from gophertalk_fastapi.service.post_service import PostService
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


@pytest.fixture
def mock_post_repository():
    """
    Provide a fully mocked `PostRepository` for service-layer testing.

    This fixture defines a mock implementation of the repository with all
    its key methods (`get_all_posts`, `create_post`, `delete_post`,
    `view_post`, `like_post`, `dislike_post`) replaced by `MagicMock`
    instances. It allows precise control over repository behavior,
    including simulating database responses or raising expected exceptions
    without requiring a real PostgreSQL connection.

    Returns:
        MagicMock: Mocked `PostRepository` object with predefined method mocks.
    """
    mock_repo = MagicMock()
    mock_repo.get_all_posts = MagicMock()
    mock_repo.create_post = MagicMock()
    mock_repo.delete_post = MagicMock()
    mock_repo.view_post = MagicMock()
    mock_repo.like_post = MagicMock()
    mock_repo.dislike_post = MagicMock()
    return mock_repo


@pytest.fixture
def post_service(mock_post_repository, mock_config):
    """
    Provide a `PostService` instance configured for isolated unit testing.

    This fixture injects a mocked `PostRepository` and mock configuration
    to test service-layer logic independently of the database layer.
    It is primarily used to validate that service methods correctly
    delegate actions to the repository and handle exceptions as expected.

    Args:
        mock_post_repository (MagicMock): Mocked `PostRepository` for database access.
        mock_config (Config): Mock configuration object with test-safe settings.

    Returns:
        PostService: Fully initialized `PostService` instance ready for testing.
    """
    return PostService(post_repository=mock_post_repository, cfg=mock_config)


@pytest.fixture
def mock_auth_service():
    """
    Provide a fully mocked `AuthService` for API route testing.

    This fixture creates a `MagicMock` instance that mimics the real
    authentication service used by the application. All public methods
    (`login`, `register`) are pre-mocked to allow fine-grained control
    over their behavior during tests — for example, returning fake tokens
    or raising expected exceptions without invoking real business logic.

    Returns:
        MagicMock: A mocked authentication service with preconfigured methods.
    """
    mock_service = MagicMock()
    mock_service.login = MagicMock()
    mock_service.register = MagicMock()
    return mock_service


@pytest.fixture
def auth_router(mock_auth_service):
    """
    Provide an `AuthRouter` instance bound to a mocked authentication service.

    This fixture constructs the router class that defines the `/auth` API endpoints,
    wiring it to a fake `AuthService`. It enables testing of HTTP route behavior
    (status codes, responses, error handling) independently of real authentication logic.

    Args:
        mock_auth_service (MagicMock): A mocked service instance used by the router.

    Returns:
        AuthRouter: Router instance with routes registered and ready for inclusion in FastAPI.
    """
    return AuthRouter(auth_service=mock_auth_service)


@pytest.fixture
def mock_user_service():
    """
    Provide a fully mocked `UserService` for isolated router testing.

    This fixture creates a `MagicMock` instance that simulates the real
    user service used by the application. All public methods
    (`get_all`, `get_by_id`, `update`, `delete`) are pre-initialized
    as mocks to allow precise control over their behavior in tests.

    It enables verification of HTTP route logic (status codes, validation,
    error handling) independently from real business logic or database access.

    Returns:
        MagicMock: Mocked user service with predefined methods for testing.
    """
    mock_service = MagicMock()
    mock_service.get_all = MagicMock()
    mock_service.get_by_id = MagicMock()
    mock_service.update = MagicMock()
    mock_service.delete = MagicMock()
    return mock_service


@pytest.fixture
def user_router(mock_user_service):
    """
    Provide a `UserRouter` instance bound to a mocked user service.

    This fixture constructs the router responsible for `/users` API endpoints,
    wiring it to a mocked `UserService`. It allows testing of HTTP routes for
    listing, retrieving, updating, and deleting users without touching the
    database or real application logic.

    Args:
        mock_user_service (MagicMock): Mocked `UserService` used by the router.

    Returns:
        UserRouter: Router instance with `/users` routes registered
        and ready for inclusion in a FastAPI app.
    """
    return UserRouter(user_service=mock_user_service)


@pytest.fixture
def test_client(auth_router, user_router):
    """
    Provide a FastAPI `TestClient` configured with the authentication router.

    This fixture creates an in-memory FastAPI application, mounts the tested router,
    and exposes a synchronous HTTP client interface for simulating requests
    to endpoints.

    It is designed for end-to-end testing of route behavior, including:
      - request validation via Pydantic models,
      - HTTP status code correctness,
      - error handling and JSON responses.

    Args:
        auth_router (AuthRouter): The router under test.
        user_router (UserRouter): The router under test.

    Returns:
        TestClient: FastAPI testing client capable of issuing real HTTP calls to the in-memory app.
    """
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(auth_router.router)
    app.include_router(user_router.router)
    return TestClient(app)
