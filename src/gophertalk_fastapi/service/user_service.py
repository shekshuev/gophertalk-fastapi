import bcrypt

from ..config.config import Config
from ..models.user import ReadUserDto, UpdateUserDto
from ..repository.user_repository import UserRepository


class UserService:
    """
    Service layer for managing user operations.

    The `UserService` acts as an intermediary between controllers and the
    `UserRepository`, applying additional business logic such as password hashing
    before performing repository actions. It encapsulates all user-related
    operations such as retrieval, update, and deletion.

    Attributes:
        user_repository (UserRepository): The repository handling database operations.
        cfg (Config): Application configuration object, primarily used for security settings.
    """

    def __init__(self, user_repository: UserRepository, cfg: Config):
        """
        Initialize the service with repository and configuration dependencies.

        Args:
            user_repository (UserRepository): Repository instance for database access.
            cfg (Config): Configuration object containing environment and security parameters.
        """
        self.user_repository = user_repository
        self.cfg = cfg

    def get_all(self, limit: int, offset: int) -> list[ReadUserDto]:
        """
        Retrieve a paginated list of all active users.

        Args:
            limit (int): Maximum number of users to return.
            offset (int): Number of users to skip (for pagination).

        Returns:
            list[ReadUserDto]: List of user DTOs representing active users.
        """
        return self.user_repository.get_all_users(limit, offset)

    def get_by_id(self, user_id: int) -> ReadUserDto:
        """
        Retrieve a single user by their unique ID.

        Args:
            user_id (int): The user’s unique identifier.

        Returns:
            ReadUserDto: DTO containing the user's data.

        Raises:
            UserNotFoundError: If no active user exists with the given ID.
        """
        return self.user_repository.get_user_by_id(user_id)

    def update(self, user_id: int, dto: UpdateUserDto) -> ReadUserDto:
        """
        Update user data, including optional password hashing.

        If the DTO includes a new password, it is securely hashed using bcrypt before
        updating the database. The plain-text password fields are cleared to prevent
        accidental persistence.

        Args:
            user_id (int): The user’s unique identifier.
            dto (UpdateUserDto): DTO containing the updated user data.

        Returns:
            ReadUserDto: DTO with updated user data.

        Raises:
            UserNotFoundError: If the user does not exist or has been deleted.
            UserRepositoryError: For any unexpected database errors.
        """
        if dto.password is not None:
            dto.password_hash = bcrypt.hashpw(dto.password.encode(), bcrypt.gensalt())
            dto.password = None
            dto.password_confirm = None

        return self.user_repository.update_user(user_id, dto)

    def delete(self, user_id: int) -> None:
        """
        Soft-delete a user by setting their `deleted_at` timestamp.

        Args:
            user_id (int): The user’s unique identifier.

        Raises:
            UserNotFoundError: If the user does not exist or is already deleted.
            UserRepositoryError: For any unexpected database errors.
        """
        return self.user_repository.delete_user(user_id)
