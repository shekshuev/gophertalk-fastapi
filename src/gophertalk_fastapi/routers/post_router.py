from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from ..config.config import Config
from ..dependencies.auth import get_current_user
from ..models.post import CreatePostDto, FilterPostDto, ReadPostDto
from ..service.post_service import PostService


class PostRouter:
    """
    Router responsible for managing posts and related interactions.

    This class defines API endpoints for working with posts:
        - Fetching a paginated list of posts with filters.
        - Creating new posts.
        - Deleting posts.
        - Viewing and liking posts.

    All endpoints rely on dependency injection for authentication
    (`get_current_user`) and delegate business logic to the `PostService`.
    """

    def __init__(self, post_service: PostService, cfg: Config):
        """
        Initialize the PostRouter with an injected service dependency.

        Args:
            post_service (PostService): Service handling post-related business logic.
            cfg (Config): App config
        """
        self.post_service = post_service
        self.cfg = cfg
        self.router = APIRouter(prefix="/posts", tags=["Posts"])
        self._register_routes()

    def _register_routes(self):
        """Register all post-related endpoints under the `/posts` prefix."""

        @self.router.get("/", response_model=List[ReadPostDto])
        def get_all_posts(
            limit: Optional[int] = Query(default=100, ge=1),
            offset: Optional[int] = Query(default=0, ge=0),
            reply_to_id: Optional[int] = Query(default=None, ge=1),
            owner_id: Optional[int] = Query(default=None, ge=1),
            search: Optional[str] = Query(default=None),
            user=Depends(get_current_user(self.cfg)),
        ):
            """
            Retrieve all posts with optional filters (pagination, search, owner, replies).

            Args:
                limit (int): Max number of posts to return.
                offset (int): Number of posts to skip.
                reply_to_id (Optional[int]): Filter by parent post.
                owner_id (Optional[int]): Filter by author.
                search (Optional[str]): Search text in posts.
                user: The currently authenticated user (injected via `Depends`).

            Returns:
                list[ReadPostDto]: A list of posts matching the filters.

            Raises:
                HTTPException: If an unexpected database or service error occurs.
            """
            try:
                filter_dto = FilterPostDto(
                    user_id=user.sub,
                    limit=limit,
                    offset=offset,
                    reply_to_id=reply_to_id,
                    owner_id=owner_id,
                    search=search,
                )
                return self.post_service.get_all_posts(filter_dto)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
                )

        @self.router.post(
            "/", response_model=ReadPostDto, status_code=status.HTTP_201_CREATED
        )
        def create_post(dto: CreatePostDto, user=Depends(get_current_user(self.cfg))):
            """
            Create a new post authored by the current user.

            Args:
                dto (CreatePostDto): DTO containing post text and optional reply target.
                user: The currently authenticated user (injected via `Depends`).

            Returns:
                ReadPostDto: The created post with metadata.

            Raises:
                HTTPException: If post creation fails (e.g., invalid parent post).
            """
            try:
                dto.user_id = user.sub
                return self.post_service.create_post(dto)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
                )

        @self.router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
        def delete_post(
            post_id: int = Path(..., gt=0), user=Depends(get_current_user(self.cfg))
        ):
            """
            Soft-delete a post belonging to the current user.

            Args:
                post_id (int): ID of the post to delete.
                user: The currently authenticated user (injected via `Depends`).

            Raises:
                HTTPException: If the post does not exist or deletion fails.
            """
            try:
                self.post_service.delete_post(post_id, user.sub)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
                )

        @self.router.post("/{post_id}/view", status_code=status.HTTP_201_CREATED)
        def view_post(
            post_id: int = Path(..., gt=0), user=Depends(get_current_user(self.cfg))
        ):
            """
            Mark a post as viewed by the current user.

            Args:
                post_id (int): ID of the post viewed.
                user: The currently authenticated user.

            Raises:
                HTTPException: If the post does not exist or view logging fails.
            """
            try:
                self.post_service.view_post(post_id, user.sub)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
                )

        @self.router.post("/{post_id}/like", status_code=status.HTTP_201_CREATED)
        def like_post(
            post_id: int = Path(..., gt=0), user=Depends(get_current_user(self.cfg))
        ):
            """
            Like a post as the current user.

            Args:
                post_id (int): ID of the post to like.
                user: The currently authenticated user.

            Raises:
                HTTPException: If the post does not exist or the like already exists.
            """
            try:
                self.post_service.like_post(post_id, user.sub)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
                )

        @self.router.delete("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
        def dislike_post(
            post_id: int = Path(..., gt=0), user=Depends(get_current_user(self.cfg))
        ):
            """
            Remove a like from a post.

            Args:
                post_id (int): ID of the post to unlike.
                user: The currently authenticated user.

            Raises:
                HTTPException: If the post does not exist or the user did not like it.
            """
            try:
                self.post_service.dislike_post(post_id, user.sub)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
                )
