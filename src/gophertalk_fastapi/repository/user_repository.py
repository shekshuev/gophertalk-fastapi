import psycopg.errors
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from ..models.user import CreateUserDto, ReadAuthUserDataDto, ReadUserDto, UpdateUserDto


class UserAlreadyExistsError(Exception):
    """
    Raised when attempting to create a new user whose username already exists.

    Typically corresponds to a `UniqueViolation` error on the `user_name` column
    in the `users` table.
    """

    ...


class UserNotFoundError(Exception):
    """
    Raised when a user cannot be found in the database.

    This can occur when:
      - The user ID or username does not exist.
      - The user has been soft-deleted (`deleted_at IS NOT NULL`).
    """

    ...


class UserRepositoryError(Exception):
    """
    General fallback exception for unexpected or unclassified database errors
    occurring in user-related queries.

    This ensures that upper layers (services, controllers) can handle all
    repository-level failures through a unified interface.
    """

    ...


class UserRepository:
    """
    Repository responsible for managing `users` and authentication-related data.

    This repository provides low-level CRUD operations for user records,
    using psycopg connection pooling and explicit SQL queries instead of an ORM.

    """

    def __init__(self, pool: ConnectionPool):
        """
        Initialize the repository with a database connection pool.

        Args:
            pool (ConnectionPool): A psycopg connection pool.
        """
        self.pool = pool

    def create_user(self, dto: CreateUserDto) -> ReadAuthUserDataDto:
        """
        Insert a new user into the database.

        Args:
            dto (CreateUserDto): Data for the new user.

        Returns:
            ReadAuthUserDataDto: The created user data including id, username, hash, and status.

        Raises:
            UserAlreadyExistsError: If username already exists.
            UserRepositoryError: For any other database error.
        """
        query = """
            INSERT INTO users (user_name, first_name, last_name, password_hash)
            VALUES (%s, %s, %s, %s)
            RETURNING id, user_name, password_hash, status;
        """
        values = (dto.user_name, dto.first_name, dto.last_name, dto.password_hash)

        try:
            with self.pool.connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(query, values)
                    row = cur.fetchone()
                    return ReadAuthUserDataDto(**row)
        except psycopg.errors.UniqueViolation as e:
            raise UserAlreadyExistsError("User already exists") from e
        except psycopg.errors.Error as e:
            raise UserRepositoryError("Unknown error") from e

    def get_all_users(self, limit: int, offset: int) -> list[ReadUserDto]:
        """
        Retrieve a paginated list of active users (not soft-deleted).

        Args:
            limit (int): Max number of users to return.
            offset (int): Number of users to skip.

        Returns:
            list[ReadUserDto]: List of user objects.

        Raises:
            UserRepositoryError: For any database error.
        """
        query = """
            SELECT id, user_name, first_name, last_name, status, created_at, updated_at
            FROM users
            WHERE deleted_at IS NULL
            OFFSET %s LIMIT %s;
        """
        params = (offset, limit)

        try:
            with self.pool.connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    return [ReadUserDto(**row) for row in rows]
        except psycopg.errors.Error as e:
            raise UserRepositoryError("Unknown error") from e

    def get_user_by_id(self, user_id: int) -> ReadUserDto:
        """
        Retrieve a user by ID.

        Args:
            user_id (int): The user's ID.

        Returns:
            ReadUserDto: User data.

        Raises:
            UserNotFoundError: If the user does not exist or is deleted.
            UserRepositoryError: For any database error.
        """
        query = """
            SELECT id, user_name, first_name, last_name, status, created_at, updated_at
            FROM users
            WHERE id = %s AND deleted_at IS NULL;
        """

        try:
            with self.pool.connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(query, (user_id,))
                    result = cur.fetchone()

                    if result is None:
                        raise UserNotFoundError("User not found")
                    return ReadUserDto(**result)
        except psycopg.errors.Error as e:
            raise UserRepositoryError("Unknown error") from e

    def get_user_by_username(self, user_name: str) -> ReadAuthUserDataDto:
        """
        Retrieve a user by username, including password hash for authentication.

        Args:
            user_name (str): The username to look up.

        Returns:
            ReadAuthUserDataDto: User data including id, username, hash, and status.

        Raises:
            UserNotFoundError: If the user does not exist or is deleted.
            UserRepositoryError: For any database error.
        """
        query = """
            SELECT id, user_name, password_hash, status
            FROM users
            WHERE user_name = %s AND deleted_at IS NULL;
        """

        try:
            with self.pool.connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(query, (user_name,))
                    result = cur.fetchone()

                    if result is None:
                        raise UserNotFoundError("User not found")
                    return ReadAuthUserDataDto(**result)
        except psycopg.errors.Error as e:
            raise UserRepositoryError("Unknown error") from e

    def update_user(self, user_id: int, dto: UpdateUserDto) -> ReadUserDto:
        """
        Update fields of an existing user.

        Args:
            user_id (int): The user's ID.
            dto (UpdateUserDto): Data with fields to update.

        Returns:
            ReadUserDto: Updated user data.

        Raises:
            UserNotFoundError: If the user does not exist or is deleted.
            UserRepositoryError: For any database error.
        """
        fields = []
        values = []

        if dto.password_hash is not None:
            fields.append("password_hash = %s")
            values.append(dto.password_hash)
        if dto.user_name is not None:
            fields.append("user_name = %s")
            values.append(dto.user_name)
        if dto.first_name is not None:
            fields.append("first_name = %s")
            values.append(dto.first_name)
        if dto.last_name is not None:
            fields.append("last_name = %s")
            values.append(dto.last_name)

        fields.append("updated_at = NOW()")
        values.append(user_id)

        query = f"""
            UPDATE users
            SET {", ".join(fields)}
            WHERE id = %s AND deleted_at IS NULL
            RETURNING id, user_name, first_name, last_name, status, created_at, updated_at;
        """

        try:
            with self.pool.connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(query, values)
                    result = cur.fetchone()

                    if result is None:
                        raise UserNotFoundError("User not found")

                    return ReadUserDto(**result)

        except psycopg.errors.Error as e:
            raise UserRepositoryError("Unknown error") from e

    def delete_user(self, user_id: int) -> None:
        """
        Soft-delete a user by setting deleted_at timestamp.

        Args:
            user_id (int): The user's ID.

        Raises:
            UserNotFoundError: If the user does not exist or is already deleted.
            UserRepositoryError: For any database error.
        """
        query = """
            UPDATE users
            SET deleted_at = NOW()
            WHERE id = %s AND deleted_at IS NULL;
        """

        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (user_id,))
                    if cur.rowcount == 0:
                        raise UserNotFoundError("User not found")

        except psycopg.errors.Error as e:
            raise UserRepositoryError("Unknown error") from e
