from typing import List

from fastapi import APIRouter, HTTPException, Path, Query, status

from ..models.user import ReadUserDto, UpdateUserDto
from ..repository.user_repository import UserNotFoundError
from ..service.user_service import UserService


class UserRouter:
    """
    Router responsible for handling user management operations.

    This router defines endpoints for retrieving, updating, and deleting users.
    It delegates all business logic to the `UserService`, serving purely as
    a transport layer between HTTP requests and the service layer.

    Routes:
        - GET /users — Retrieve a paginated list of users.
        - GET /users/{user_id} — Retrieve a single user by ID.
        - PUT /users/{user_id} — Update an existing user.
        - DELETE /users/{user_id} — Soft-delete a user.

    All exceptions raised by the service layer are converted into HTTP responses
    with appropriate status codes and error messages.
    """

    def __init__(self, user_service: UserService):
        """
        Initialize the router with the user service dependency.

        Args:
            user_service (UserService): Service layer responsible for
                user data access and business logic.
        """
        self.user_service = user_service
        self.router = APIRouter(prefix="/users", tags=["Users"])
        self._register_routes()

    def _register_routes(self):
        """Register all user-related API routes under `/users` prefix."""

        @self.router.get(
            "/",
            response_model=List[ReadUserDto],
            status_code=status.HTTP_200_OK,
        )
        def get_all(limit: int = Query(10, ge=1), offset: int = Query(0, ge=0)):
            """
            Retrieve a paginated list of all active (non-deleted) users.

            Args:
                limit (int): Maximum number of users to return per request (default: 10).
                offset (int): Number of users to skip for pagination (default: 0).

            Returns:
                List[ReadUserDto]: List of user DTOs representing the active users.

            Raises:
                HTTPException: If any unexpected error occurs in the service layer.
            """
            try:
                return self.user_service.get_all(limit, offset)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
                )

        @self.router.get(
            "/{user_id}",
            response_model=ReadUserDto,
            status_code=status.HTTP_200_OK,
        )
        def get_by_id(user_id: int = Path(..., gt=0)):
            """
            Retrieve a user by their unique identifier.

            Args:
                user_id (int): The unique identifier of the user (must be positive).

            Returns:
                ReadUserDto: The user data corresponding to the given ID.

            Raises:
                HTTPException: 404 if the user does not exist.
            """
            try:
                return self.user_service.get_by_id(user_id)
            except UserNotFoundError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
                )

        @self.router.put(
            "/{user_id}",
            response_model=ReadUserDto,
            status_code=status.HTTP_200_OK,
        )
        def update_by_id(user_id: int, dto: UpdateUserDto):
            """
            Update an existing user's data.

            Args:
                user_id (int): The ID of the user to update.
                dto (UpdateUserDto): DTO containing fields to update (e.g. names, password).

            Returns:
                ReadUserDto: The updated user data.

            Raises:
                HTTPException: 400 if validation fails or update is invalid.
            """
            try:
                return self.user_service.update(user_id, dto)
            except UserNotFoundError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
                )

        @self.router.delete(
            "/{user_id}",
            status_code=status.HTTP_204_NO_CONTENT,
        )
        def delete_by_id(user_id: int = Path(..., gt=0)):
            """
            Soft-delete a user by setting their `deleted_at` timestamp.

            Args:
                user_id (int): The ID of the user to delete (must be positive).

            Raises:
                HTTPException: 404 if the user does not exist or is already deleted.
            """
            try:
                self.user_service.delete(user_id)
            except UserNotFoundError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
                )
