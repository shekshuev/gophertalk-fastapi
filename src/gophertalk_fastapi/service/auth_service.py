from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from ..config.config import Config
from ..models.auth import LoginUserDto, ReadTokenDto, RegisterUserDto
from ..models.user import CreateUserDto
from ..repository.user_repository import UserRepository


class WrongPasswordError(Exception):
    """Raised when the provided password does not match the stored hash."""

    ...


class AuthService:
    """
    Service responsible for user authentication and token management.

    Provides methods for user login, registration, and generation of JWT token pairs.
    """

    def __init__(self, user_repository: UserRepository, cfg: Config):
        """
        Initialize the authentication service.

        Args:
            user_repository (UserRepository): Repository instance for user data access.
            cfg (Config): Application configuration object containing JWT secrets and expiration times.
        """
        self.user_repository = user_repository
        self.cfg = cfg

    def login(self, dto: LoginUserDto) -> ReadTokenDto:
        """
        Authenticate a user using their username and password.

        Args:
            dto (LoginUserDto): DTO containing username and plaintext password.

        Returns:
            ReadTokenDto: Object containing generated access and refresh tokens.

        Raises:
            WrongPasswordError: If the password does not match the stored hash.
            UserNotFoundError: If the username does not exist (raised by the repository).
            UserRepositoryError: For unexpected database errors.
        """
        user = self.user_repository.get_user_by_username(dto.user_name)

        if not bcrypt.checkpw(dto.password.encode(), user.password_hash.encode()):
            raise WrongPasswordError("Wrong password")

        return self.generate_token_pair(user.id)

    def register(self, dto: RegisterUserDto) -> ReadTokenDto:
        """
        Register a new user in the system and return JWT tokens.

        Args:
            dto (RegisterUserDto): DTO containing username, password, and optional profile fields.

        Returns:
            ReadTokenDto: Object containing generated access and refresh tokens.

        Raises:
            UserAlreadyExistsError: If the username is already taken.
            UserRepositoryError: For unexpected database errors.
        """
        password_hash = bcrypt.hashpw(dto.password.encode(), bcrypt.gensalt()).decode()

        user_data = CreateUserDto(
            user_name=dto.user_name,
            password_hash=password_hash,
            first_name=dto.first_name,
            last_name=dto.last_name,
        )
        user = self.user_repository.create_user(user_data)
        return self.generate_token_pair(user.id)

    def generate_token_pair(self, user_id: int) -> ReadTokenDto:
        """
        Generate a new pair of JWT tokens (access and refresh) for a user.

        Args:
            user_id (int): ID of the authenticated user.

        Returns:
            ReadTokenDto: DTO containing both access and refresh tokens.

        Token Details:
            - Access Token: Short-lived (used for API requests).
            - Refresh Token: Longer-lived (used to obtain new access tokens).
        """
        now = datetime.now(timezone.utc)

        print(self.cfg)

        access_token = jwt.encode(
            {
                "sub": str(user_id),
                "exp": now + timedelta(seconds=self.cfg.access_token_expires),
                "type": "access",
            },
            self.cfg.access_token_secret,
            algorithm=self.cfg.hash_algorithm,
        )

        refresh_token = jwt.encode(
            {
                "sub": str(user_id),
                "exp": now + timedelta(seconds=self.cfg.refresh_token_expires),
                "type": "refresh",
            },
            self.cfg.refresh_token_secret,
            algorithm=self.cfg.hash_algorithm,
        )

        return ReadTokenDto(access_token=access_token, refresh_token=refresh_token)
