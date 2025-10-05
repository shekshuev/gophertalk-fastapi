from ..config.config import Config
from ..models.post import CreatePostDto, FilterPostDto, ReadPostDto
from ..repository.post_repository import PostRepository


class PostService:
    """
    Service layer responsible for handling post-related operations.

    This class acts as an intermediary between controllers (API layer)
    and the repository layer, providing a clean interface for managing
    posts, likes, views, and deletions.

    """

    def __init__(self, post_repository: PostRepository, cfg: Config):
        """
        Initialize the PostService with repository and configuration.

        Args:
            post_repository (PostRepository): Repository instance for post-related DB operations.
            cfg (Config): Application configuration (used for future extensions such as caching or limits).
        """
        self.post_repository = post_repository
        self.cfg = cfg

    def get_all_posts(self, filter_dto: FilterPostDto) -> list[ReadPostDto]:
        """
        Retrieve a list of posts based on given filter criteria.

        Delegates filtering, pagination, and search logic to the repository.

        Args:
            filter_dto (FilterPostDto): Filter parameters including search term, pagination, and ownership filters.

        Returns:
            list[ReadPostDto]: List of posts matching the filter criteria.

        Raises:
            PostRepositoryError: For unexpected database-level errors.
        """
        return self.post_repository.get_all_posts(filter_dto)

    def create_post(self, create_dto: CreatePostDto) -> ReadPostDto:
        """
        Create a new post.

        Args:
            create_dto (CreatePostDto): DTO containing post text, user ID, and optional reply_to_id.

        Returns:
            ReadPostDto: The created post's data (id, text, author, created_at, etc.).

        Raises:
            ReplyToPostDoesNotExistsError: If the reply target does not exist.
            PostRepositoryError: For unexpected database-level errors.
        """
        return self.post_repository.create_post(create_dto)

    def delete_post(self, post_id: int, owner_id: int) -> None:
        """
        Soft-delete a post by its ID.

        Args:
            post_id (int): ID of the post to delete.
            owner_id (int): ID of the post’s author, used for ownership validation.

        Raises:
            PostNotFoundError: If the post is not found or already deleted.
            PostRepositoryError: For unexpected database-level errors.
        """
        return self.post_repository.delete_post(post_id, owner_id)

    def view_post(self, post_id: int, user_id: int) -> None:
        """
        Mark a post as viewed by the given user.

        Args:
            post_id (int): ID of the viewed post.
            user_id (int): ID of the user performing the view.

        Raises:
            PostAlreadyViewedError: If the post has already been viewed by the user.
            PostRepositoryError: For unexpected database-level errors.
        """
        return self.post_repository.view_post(post_id, user_id)

    def like_post(self, post_id: int, user_id: int) -> None:
        """
        Mark a post as liked by the given user.

        Args:
            post_id (int): ID of the liked post.
            user_id (int): ID of the user liking the post.

        Raises:
            PostAlreadyLikedError: If the post has already been liked by the user.
            PostRepositoryError: For unexpected database-level errors.
        """
        return self.post_repository.like_post(post_id, user_id)

    def dislike_post(self, post_id: int, user_id: int) -> None:
        """
        Remove the user's like from a post.

        Args:
            post_id (int): ID of the post to unlike.
            user_id (int): ID of the user removing the like.

        Raises:
            PostRepositoryError: For unexpected database-level errors.
        """
        return self.post_repository.dislike_post(post_id, user_id)
