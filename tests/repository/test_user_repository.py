import re

import psycopg
import pytest
from pydantic import ValidationError

from gophertalk_fastapi.models.user import (
    CreateUserDto,
    ReadAuthUserDataDto,
    ReadUserDto,
    UpdateUserDto,
)
from gophertalk_fastapi.repository.user_repository import (
    UserAlreadyExistsError,
    UserNotFoundError,
    UserRepositoryError,
)


def test_create_user_success(user_repository, mock_pool):
    """
    Test that `create_user()` successfully inserts a new user into the database.

    This test verifies:
      - The repository executes the expected SQL INSERT statement.
      - The correct parameter values are passed to the query.
      - The method returns a valid `ReadAuthUserDataDto` object with correct data.

    Steps:
      1. Mock the cursor's `fetchone()` to simulate a DB returning a new user row.
      2. Call `create_user()` with a valid DTO.
      3. Assert the returned object and SQL execution details.
    """
    dto = CreateUserDto(
        user_name="john_doe",
        first_name="John",
        last_name="Doe",
        password_hash="hashed123",
    )

    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.fetchone.return_value = {
        "id": 1,
        "user_name": "john_doe",
        "password_hash": "hashed123",
        "status": 1,
    }

    result = user_repository.create_user(dto)

    assert isinstance(result, ReadAuthUserDataDto)
    assert result.user_name == "john_doe"

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]
    assert "INSERT INTO users" in sql
    assert params == ("john_doe", "John", "Doe", "hashed123")


def test_create_user_unique_violation(user_repository, mock_pool):
    """
    Test that `create_user()` raises `UserAlreadyExistsError` when a unique
    constraint violation occurs (duplicate username).

    Steps:
      1. Mock `execute()` to raise `psycopg.errors.UniqueViolation`.
      2. Ensure `UserAlreadyExistsError` is raised.
    """
    dto = CreateUserDto(
        user_name="john_doe",
        first_name="John",
        last_name="Doe",
        password_hash="hashed123",
    )

    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.UniqueViolation("duplicate key")

    with pytest.raises(UserAlreadyExistsError):
        user_repository.create_user(dto)


def test_create_user_unknown_error(user_repository, mock_pool):
    """
    Test that `create_user()` raises `UserRepositoryError` for unknown database errors.

    Steps:
      1. Mock `execute()` to raise a generic `psycopg.errors.Error`.
      2. Ensure `UserRepositoryError` is raised.
    """
    dto = CreateUserDto(
        user_name="john_doe",
        first_name="John",
        last_name="Doe",
        password_hash="hashed123",
    )

    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.Error("connection failure")

    with pytest.raises(UserRepositoryError):
        user_repository.create_user(dto)


def test_get_all_users_success(user_repository, mock_pool):
    """
    Test that `get_all_users()` successfully retrieves a paginated list of users.

    This test verifies:
      - The repository executes the expected SQL SELECT query.
      - The method returns a list of `ReadUserDto` objects.
      - The SQL query includes correct pagination parameters (OFFSET and LIMIT).

    Steps:
      1. Mock the cursor's `fetchall()` to return a list of user rows.
      2. Call `get_all_users()` with `limit` and `offset`.
      3. Assert that the returned list matches the expected data and structure.
      4. Verify the executed SQL and parameters.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.fetchall.return_value = [
        {
            "id": 1,
            "user_name": "alice",
            "first_name": "Alice",
            "last_name": "Smith",
            "status": 1,
            "created_at": "2025-10-05T00:00:00Z",
            "updated_at": "2025-10-05T00:00:00Z",
        },
        {
            "id": 2,
            "user_name": "bob",
            "first_name": "Bob",
            "last_name": "Brown",
            "status": 1,
            "created_at": "2025-10-05T00:00:00Z",
            "updated_at": "2025-10-05T00:00:00Z",
        },
    ]

    limit = 10
    offset = 5
    result = user_repository.get_all_users(limit=limit, offset=offset)

    assert isinstance(result, list)
    assert all(isinstance(u, ReadUserDto) for u in result)
    assert result[0].user_name == "alice"

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]
    assert re.search(
        r"select\s+id.*from\s+users.+deleted_at\s+is\s+null",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    )

    assert params == (offset, limit)


def test_get_all_users_database_error(user_repository, mock_pool):
    """
    Test that `get_all_users()` raises `UserRepositoryError`
    when a database error occurs during query execution.

    Steps:
      1. Mock `execute()` to raise `psycopg.errors.Error`.
      2. Assert that `UserRepositoryError` is raised.
    """

    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.Error("database error")

    with pytest.raises(UserRepositoryError):
        user_repository.get_all_users(limit=10, offset=0)


def test_get_user_by_id_success(user_repository, mock_pool):
    """
    Test that `get_user_by_id()` successfully retrieves a user by ID.

    This test verifies:
      - The repository executes the expected SELECT query.
      - The returned result is an instance of `ReadUserDto`.
      - The correct SQL parameters are passed.

    Steps:
      1. Mock the cursor's `fetchone()` to return a valid user row.
      2. Call `get_user_by_id()` with a test user ID.
      3. Assert that the returned DTO contains correct data.
      4. Verify that the SQL query structure and parameters are correct.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.fetchone.return_value = {
        "id": 1,
        "user_name": "john_doe",
        "first_name": "John",
        "last_name": "Doe",
        "status": 1,
        "created_at": "2025-10-05T00:00:00Z",
        "updated_at": "2025-10-05T00:00:00Z",
    }
    user_id = 1
    result = user_repository.get_user_by_id(user_id)

    assert isinstance(result, ReadUserDto)
    assert result.user_name == "john_doe"

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]

    assert re.search(
        r"select\s+id.*from\s+users.*id\s*=\s*%s.*",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    )
    assert re.search(
        r"select\s+id.*from\s+users.*deleted_at\s+is\s+null.*",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    )

    assert params == (user_id,)


def test_get_user_by_id_not_found(user_repository, mock_pool):
    """
    Test that `get_user_by_id()` raises `UserNotFoundError` when no user is found.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.fetchone.return_value = None

    with pytest.raises(UserNotFoundError):
        user_repository.get_user_by_id(999)

    mock_cursor.execute.assert_called_once()


def test_get_user_by_id_unknown_error(user_repository, mock_pool):
    """
    Test that `get_user_by_id()` raises `UserRepositoryError` on unexpected DB exceptions.
    """

    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.Error("connection lost")

    with pytest.raises(UserRepositoryError):
        user_repository.get_user_by_id(1)


def test_get_user_by_username_success(user_repository, mock_pool):
    """
    Test that `get_user_by_username()` successfully retrieves a user by username.

    This test verifies:
      - The repository executes the expected SELECT query.
      - The returned result is a valid `ReadAuthUserDataDto`.
      - SQL query includes correct WHERE conditions for username and deleted_at.

    Steps:
      1. Mock the cursor's `fetchone()` to return a fake user row.
      2. Call `get_user_by_username()` with a test username.
      3. Assert that the returned object matches expected fields.
      4. Verify SQL text and parameters passed to the cursor.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.fetchone.return_value = {
        "id": 42,
        "user_name": "alice",
        "password_hash": "hashed_pw",
        "status": 1,
    }

    user_name = "alice"
    result = user_repository.get_user_by_username(user_name)

    assert isinstance(result, ReadAuthUserDataDto)
    assert result.user_name == "alice"
    assert result.password_hash == "hashed_pw"

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]

    assert re.search(
        r"select\s+id.*user_name.*password_hash.*from\s+users",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    )
    assert re.search(
        r"user_name\s*=\s*%s",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    )
    assert re.search(
        r"deleted_at\s+is\s+null",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    )

    assert params == (user_name,)


def test_get_user_by_username_not_found(user_repository, mock_pool):
    """
    Test that `get_user_by_username()` raises `UserNotFoundError`
    when the user does not exist or is soft-deleted.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.fetchone.return_value = None
    with pytest.raises(UserNotFoundError):
        user_repository.get_user_by_username("ghost")


def test_get_user_by_username_db_error(user_repository, mock_pool):
    """
    Test that `get_user_by_username()` raises `UserRepositoryError`
    when a generic database error occurs.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.Error("connection lost")

    with pytest.raises(UserRepositoryError):
        user_repository.get_user_by_username("fail_user")


def test_update_user_success(user_repository, mock_pool):
    """
    Test that `update_user()` successfully updates user data.

    Verifies:
      - Model validation passes for correct input.
      - SQL query is dynamically constructed with correct fields.
      - Result is a valid `ReadUserDto`.

    Steps:
      1. Create a valid `UpdateUserDto`.
      2. Mock the cursor's return value with updated user data.
      3. Call `update_user()` and verify result + SQL structure.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.fetchone.return_value = {
        "id": 1,
        "user_name": "new_user",
        "first_name": "John",
        "last_name": "Doe",
        "status": 1,
        "created_at": "2025-10-05T00:00:00Z",
        "updated_at": "2025-10-05T01:00:00Z",
    }

    dto = UpdateUserDto(
        user_name="new_user",
        first_name="John",
        last_name="Doe",
        password="StrongP@ss1",
        password_confirm="StrongP@ss1",
        password_hash="hashed123",
    )

    user_id = 1
    result = user_repository.update_user(user_id=user_id, dto=dto)

    assert isinstance(result, ReadUserDto)
    assert result.user_name == "new_user"

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]

    assert re.search(r"update\s+users\s+set", sql, re.IGNORECASE)
    assert re.search(r"user_name\s*=\s*%s", sql, re.IGNORECASE)
    assert re.search(r"first_name\s*=\s*%s", sql, re.IGNORECASE)
    assert re.search(r"last_name\s*=\s*%s", sql, re.IGNORECASE)
    assert re.search(r"updated_at\s*=\s*now\(\)", sql, re.IGNORECASE)
    assert re.search(r"where\s+id\s*=\s*%s", sql, re.IGNORECASE)
    assert re.search(r"deleted_at\s+is\s+null", sql, re.IGNORECASE)

    assert params[-1] == user_id


def test_update_user_password_mismatch():
    """
    Test that model validation fails when `password` and `password_confirm` don't match.
    """
    with pytest.raises(ValidationError) as exc_info:
        UpdateUserDto(
            user_name="user5",
            first_name="Alice",
            last_name="Smith",
            password="Qwerty123!",
            password_confirm="Qwerty321!",
            password_hash="hash",
        )
    assert "Passwords does not match" in str(exc_info.value)


def test_update_user_invalid_username():
    """
    Test that invalid usernames (starting with digits, special chars, etc.) fail validation.
    """
    with pytest.raises(ValidationError):
        UpdateUserDto(
            user_name="1bad_user",
            first_name="John",
            last_name="Doe",
            password="P@ssw0rd",
            password_confirm="P@ssw0rd",
            password_hash="hash",
        )


def test_update_user_invalid_name():
    """
    Test that invalid characters in first or last name raise validation errors.
    """
    with pytest.raises(ValidationError):
        UpdateUserDto(
            user_name="gooduser",
            first_name="J0hn",
            last_name="Doe",
            password="P@ssw0rd",
            password_confirm="P@ssw0rd",
            password_hash="hash",
        )


def test_update_user_not_found(user_repository, mock_pool):
    """
    Test that `update_user()` raises `UserNotFoundError`
    when no user row is updated or returned.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
    mock_cursor.fetchone.return_value = None

    dto = UpdateUserDto(
        user_name="ghost",
        first_name="Ghost",
        last_name="User",
        password="StrongP@ss1",
        password_confirm="StrongP@ss1",
        password_hash="hash",
    )

    with pytest.raises(UserNotFoundError):
        user_repository.update_user(user_id=999, dto=dto)


def test_update_user_db_error(user_repository, mock_pool):
    """
    Test that `update_user()` raises `UserRepositoryError`
    when a database exception occurs.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.Error("syntax error in SQL")

    dto = UpdateUserDto(
        user_name="user1",
        first_name="John",
        last_name="Doe",
        password="StrongP@ss1",
        password_confirm="StrongP@ss1",
        password_hash="hash",
    )

    with pytest.raises(UserRepositoryError):
        user_repository.update_user(user_id=1, dto=dto)


def test_delete_user_success(user_repository, mock_pool):
    """
    Test that `delete_user()` performs a soft delete successfully.

    This test verifies:
      - The repository executes the correct UPDATE query.
      - The query includes the correct `WHERE` and `SET` clauses.
      - No exceptions are raised for a valid deletion.

    Steps:
      1. Mock the cursor's `rowcount` to simulate one updated row.
      2. Call `delete_user()` with a valid user ID.
      3. Assert that the correct SQL query and parameters were used.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.rowcount = 1
    user_id = 42

    user_repository.delete_user(user_id)

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]

    assert re.search(
        r"update\s+users.*set\s+deleted_at\s*=\s*now",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    ), f"SQL missing SET deleted_at clause:\n{sql}"

    assert re.search(
        r"where\s+id\s*=\s*%s.*deleted_at\s+is\s+null",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    ), f"SQL missing WHERE id and deleted_at filter:\n{sql}"

    assert params == (user_id,)


def test_delete_user_not_found(user_repository, mock_pool):
    """
    Test that `delete_user()` raises UserNotFoundError when no rows are affected.

    Steps:
      1. Mock cursor to return `rowcount = 0`.
      2. Call `delete_user()` with a non-existent user ID.
      3. Expect `UserNotFoundError` to be raised.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.rowcount = 0
    user_id = 999

    with pytest.raises(UserNotFoundError):
        user_repository.delete_user(user_id)


def test_delete_user_unknown_error(user_repository, mock_pool):
    """
    Test that `delete_user()` raises UserRepositoryError for generic DB failures.

    Steps:
      1. Mock cursor.execute() to raise a psycopg generic error.
      2. Call `delete_user()`.
      3. Expect `UserRepositoryError` to be raised.
    """
    mock_cursor = mock_pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    mock_cursor.execute.side_effect = psycopg.errors.Error("connection lost")

    with pytest.raises(UserRepositoryError):
        user_repository.delete_user(10)
