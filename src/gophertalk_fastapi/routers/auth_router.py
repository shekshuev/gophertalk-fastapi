from fastapi import APIRouter, HTTPException, status

from ..models.auth import LoginUserDto, ReadTokenDto, RegisterUserDto
from ..service.auth_service import AuthService, WrongPasswordError


class AuthRouter:
    """
    Router responsible for handling user authentication and registration routes.

    This class defines API endpoints for user login and registration, delegating
    business logic to the `AuthService`. It serves as the boundary between HTTP
    requests and the application’s authentication layer.

    Routes:
        - POST /auth/login — Authenticate user credentials and return JWT tokens.
        - POST /auth/register — Register a new user and return JWT tokens.

    The router converts service-layer errors (e.g. `WrongPasswordError`)
    into structured HTTP responses.
    """

    def __init__(self, auth_service: AuthService):
        """
        Initialize the router with a service dependency.

        Args:
            auth_service (AuthService): The authentication service that implements
                business logic for login, registration, and token handling.
        """
        self.auth_service = auth_service
        self.router = APIRouter(prefix="/auth", tags=["Auth"])
        self._register_routes()

    def _register_routes(self):
        """Register all authentication-related routes under `/auth` prefix."""

        @self.router.post(
            "/login", response_model=ReadTokenDto, status_code=status.HTTP_200_OK
        )
        def login(dto: LoginUserDto):
            """
            Authenticate a user by verifying credentials and returning a token pair.

            Args:
                dto (LoginUserDto): User-provided credentials (username and password).

            Returns:
                ReadTokenDto: JWT access and refresh tokens.

            Raises:
                HTTPException: If authentication fails (invalid credentials).
            """
            try:
                return self.auth_service.login(dto)
            except WrongPasswordError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
                )

        @self.router.post(
            "/register",
            response_model=ReadTokenDto,
            status_code=status.HTTP_201_CREATED,
        )
        def register(dto: RegisterUserDto):
            """
            Register a new user and return a token pair upon success.

            Args:
                dto (RegisterUserDto): Registration data including username,
                    password, and optional name fields.

            Returns:
                ReadTokenDto: JWT access and refresh tokens for the newly created user.

            Raises:
                HTTPException: If registration fails (e.g. duplicate username).
            """
            try:
                return self.auth_service.register(dto)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
                )
