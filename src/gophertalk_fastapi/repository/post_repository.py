import psycopg.errors
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from ..models.post import CreatePostDto, FilterPostDto, ReadPostDto, ReadPostUserDto


class ReplyToPostDoesNotExistsError(Exception):
    """
    Raised when a post creation attempt references a `reply_to_id`
    that does not exist in the database.

    Typically triggered by a `ForeignKeyViolation` in PostgreSQL
    when the user replies to a non-existent post.
    """

    ...


class PostNotFoundError(Exception):
    """
    Raised when a requested post cannot be found.

    This may occur when:
      - The post ID does not exist in the database.
      - The post has been soft-deleted (i.e., `deleted_at` is not NULL).
    """

    ...


class PostAlreadyViewedError(Exception):
    """
    Raised when a user attempts to mark a post as viewed
    but a corresponding entry in the `views` table already exists.
    """

    ...


class PostAlreadyLikedError(Exception):
    """
    Raised when a user tries to like a post that has already been liked.

    Typically corresponds to a `UniqueViolation` of the primary key
    constraint in the `likes` table (`pk__likes`).
    """

    ...


class PostRepositoryError(Exception):
    """
    General fallback exception for unexpected database-related errors.

    This exception acts as a catch-all for unclassified PostgreSQL errors,
    providing a consistent error interface for higher-level services.
    """

    ...


class PostRepository:
    """
    Repository responsible for managing `posts` and related actions.

    This class provides direct database access for all post-related operations,
    including creation, retrieval, deletion, and like/view management.
    All database interactions are performed using `psycopg` with connection
    pooling (`psycopg_pool.ConnectionPool`) and context managers for safety.

    The repository handles both direct CRUD operations and computed data,
    such as counts of likes, views, replies, and per-user interaction flags.

    """

    def __init__(self, pool: ConnectionPool):
        """
        Initialize the repository with a database connection pool.

        Args:
            pool (ConnectionPool): A psycopg connection pool.
        """
        self.pool = pool

    def create_post(self, dto: CreatePostDto) -> ReadPostDto:
        """
        Create a new post in the database.

        Args:
            dto (CreatePostDto): Data Transfer Object containing post content,
                the user ID, and optional reply-to post ID.

        Returns:
            ReadPostDto: DTO with created post's data (id, text, user_id, reply_to_id, created_at).

        Raises:
            ReplyToPostDoesNotExistsError: If reply_to_id refers to a non-existent post.
            PostRepositoryError: For any other unexpected database errors.
        """
        query = """
            INSERT INTO posts (text, user_id, reply_to_id)
            VALUES (%s, %s, %s)
            RETURNING id, text, user_id, reply_to_id, created_at;
        """
        values = (
            dto.text,
            dto.user_id,
            dto.reply_to_id,
        )

        try:
            with self.pool.connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(query, values)
                    row = cur.fetchone()
                    return ReadPostDto(**row)
        except psycopg.errors.ForeignKeyViolation as e:
            raise ReplyToPostDoesNotExistsError("Reply to post doesn't exists") from e
        except psycopg.errors.Error as e:
            raise PostRepositoryError("Unknown error") from e

    def get_all_posts(self, dto: FilterPostDto) -> list[ReadPostDto]:
        """
        Retrieve a paginated list of posts matching the provided filter criteria.

        Args:
            dto (FilterPostDto): DTO containing filters such as search term,
                owner_id, reply_to_id, user_id (for liked/viewed flags), offset, and limit.

        Returns:
            list[ReadPostDto]: List of posts with aggregated likes, views, replies,
                and flags indicating if the requesting user liked or viewed them.

        Raises:
            PostRepositoryError: For any unexpected database errors.
        """
        params = [dto.user_id, dto.user_id]
        query = """
            WITH likes_count AS (
                SELECT post_id, COUNT(*) AS likes_count
                FROM likes GROUP BY post_id
            ),
            views_count AS (
                SELECT post_id, COUNT(*) AS views_count
                FROM views GROUP BY post_id
            ),
            replies_count AS (
                SELECT reply_to_id, COUNT(*) AS replies_count
                FROM posts WHERE reply_to_id IS NOT NULL GROUP BY reply_to_id
            )
            SELECT
                p.id, p.text, p.reply_to_id, p.created_at,
                u.id AS user_id, u.user_name, u.first_name, u.last_name,
                COALESCE(lc.likes_count, 0) AS likes_count,
                COALESCE(vc.views_count, 0) AS views_count,
                COALESCE(rc.replies_count, 0) AS replies_count,
                CASE WHEN l.user_id IS NOT NULL THEN true ELSE false END AS user_liked,
                CASE WHEN v.user_id IS NOT NULL THEN true ELSE false END AS user_viewed
            FROM posts p
            JOIN users u ON p.user_id = u.id
            LEFT JOIN likes_count lc ON p.id = lc.post_id
            LEFT JOIN views_count vc ON p.id = vc.post_id
            LEFT JOIN replies_count rc ON p.id = rc.reply_to_id
            LEFT JOIN likes l ON l.post_id = p.id AND l.user_id = %s
            LEFT JOIN views v ON v.post_id = p.id AND v.user_id = %s
            WHERE p.deleted_at IS NULL
        """

        if dto.search is not None:
            query += " AND p.text ILIKE %s"
            params.append(f"%{dto.search}%")

        if dto.owner_id is not None:
            query += " AND p.user_id = %s"
            params.append(dto.owner_id)

        if dto.reply_to_id is not None:
            query += " AND p.reply_to_id = %s ORDER BY p.created_at ASC"
            params.append(dto.reply_to_id)
        else:
            query += " AND p.reply_to_id IS NULL ORDER BY p.created_at DESC"

        query += " OFFSET %s LIMIT %s"
        params.extend([dto.offset, dto.limit])

        try:
            with self.pool.connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    return [
                        ReadPostDto(
                            id=row["id"],
                            text=row["text"],
                            reply_to_id=row["reply_to_id"],
                            created_at=row["created_at"],
                            likes_count=row["likes_count"],
                            views_count=row["views_count"],
                            replies_count=row["replies_count"],
                            user_liked=row["user_liked"],
                            user_viewed=row["user_viewed"],
                            user_id=row["user_id"],
                            user=ReadPostUserDto(
                                id=row["user_id"],
                                user_name=row["user_name"],
                                first_name=row["first_name"],
                                last_name=row["last_name"],
                            ),
                        )
                        for row in rows
                    ]
        except psycopg.errors.Error as e:
            raise PostRepositoryError("Unknown error") from e

    def get_post_by_id(self, post_id: int, user_id: int) -> ReadPostDto:
        """
        Retrieve a single post by its ID, including aggregated likes, views,
        replies, and flags indicating if the requesting user liked or viewed it.

        Args:
            post_id (int): ID of the post to retrieve.
            user_id (int): ID of the user requesting the post (used to check like/view flags).

        Returns:
            ReadPostDto: DTO with the post data and aggregated metrics.

        Raises:
            PostNotFoundError: If no post exists with the given ID.
            PostRepositoryError: For any unexpected database errors.
        """
        query = """
            WITH likes_count AS (
                SELECT post_id, COUNT(*) AS likes_count
                FROM likes
                GROUP BY post_id
            ),
            views_count AS (
                SELECT post_id, COUNT(*) AS views_count
                FROM views
                GROUP BY post_id
            ),
            replies_count AS (
                SELECT reply_to_id, COUNT(*) AS replies_count
                FROM posts
                WHERE reply_to_id IS NOT NULL
                GROUP BY reply_to_id
            )
            SELECT
                p.id AS post_id,
                p.text,
                p.reply_to_id,
                p.created_at,
                u.id AS user_id,
                u.user_name,
                u.first_name,
                u.last_name,
                COALESCE(lc.likes_count, 0) AS likes_count,
                COALESCE(vc.views_count, 0) AS views_count,
                COALESCE(rc.replies_count, 0) AS replies_count,
                CASE WHEN l.user_id IS NOT NULL THEN true ELSE false END AS user_liked,
                CASE WHEN v.user_id IS NOT NULL THEN true ELSE false END AS user_viewed
            FROM posts p
            JOIN users u ON p.user_id = u.id
            LEFT JOIN likes_count lc ON p.id = lc.post_id
            LEFT JOIN views_count vc ON p.id = vc.post_id
            LEFT JOIN replies_count rc ON p.id = rc.reply_to_id
            LEFT JOIN likes l ON l.post_id = p.id AND l.user_id = %s
            LEFT JOIN views v ON v.post_id = p.id AND v.user_id = %s
            WHERE p.id = %s AND p.deleted_at IS NULL;
        """
        params = (user_id, user_id, post_id)

        try:
            with self.pool.connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(query, params)
                    row = cur.fetchone()

                    if row is None:
                        raise PostNotFoundError("Post not found")

                    return ReadPostDto(
                        id=row["post_id"],
                        text=row["text"],
                        reply_to_id=row["reply_to_id"],
                        created_at=row["created_at"],
                        likes_count=row["likes_count"],
                        views_count=row["views_count"],
                        replies_count=row["replies_count"],
                        user_liked=row["user_liked"],
                        user_viewed=row["user_viewed"],
                        user_id=row["user_id"],
                        user=ReadPostUserDto(
                            id=row["user_id"],
                            user_name=row["user_name"],
                            first_name=row["first_name"],
                            last_name=row["last_name"],
                        ),
                    )
        except psycopg.errors.Error as e:
            raise PostRepositoryError("Unknown error") from e

    def delete_post(self, post_id: int, owner_id: int) -> None:
        """
        Soft delete a post by setting its deleted_at timestamp.

        Args:
            post_id (int): ID of the post to delete.
            owner_id (int): ID of the post owner (ensures user can only delete own posts).

        Raises:
            PostNotFoundError: If no matching post exists or it's already deleted.
            PostRepositoryError: For any unexpected database errors.
        """
        query = """
            UPDATE posts
            SET deleted_at = NOW()
            WHERE id = %s AND user_id = %s AND deleted_at IS NULL;
        """
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (post_id, owner_id))
                    if cur.rowcount == 0:
                        raise PostNotFoundError("Post not found or already deleted")
        except psycopg.errors.Error as e:
            raise PostRepositoryError("Unknown error") from e

    def view_post(self, post_id: int, user_id: int) -> None:
        """
        Mark a post as viewed by inserting a record into the views table.

        Args:
            post_id (int): ID of the post viewed.
            user_id (int): ID of the user viewing the post.

        Raises:
            PostAlreadyViewedError: If the user already viewed the post.
            PostRepositoryError: For user/post not found or unexpected database errors.
        """
        query = """
            INSERT INTO views (post_id, user_id)
            VALUES (%s, %s);
        """
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (post_id, user_id))
                    if cur.rowcount == 0:
                        raise PostNotFoundError("Post not found")
        except psycopg.errors.ForeignKeyViolation as e:
            raise PostRepositoryError("User or post not found") from e
        except psycopg.errors.UniqueViolation as e:
            if "pk__views" in str(e):
                raise PostAlreadyViewedError("Post already viewed") from e
            raise PostRepositoryError("Unknown error") from e
        except psycopg.errors.Error as e:
            raise PostRepositoryError("Unknown error") from e

    def like_post(self, post_id: int, user_id: int) -> None:
        """
        Mark a post as liked by inserting a record into the likes table.

        Args:
            post_id (int): ID of the post to like.
            user_id (int): ID of the user liking the post.

        Raises:
            PostAlreadyLikedError: If the user already liked the post.
            PostRepositoryError: For user/post not found or unexpected database errors.
        """
        query = """
            INSERT INTO likes (post_id, user_id)
            VALUES (%s, %s)
        """

        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (post_id, user_id))
        except psycopg.errors.ForeignKeyViolation as e:
            raise PostRepositoryError("User or post not found") from e
        except psycopg.errors.UniqueViolation as e:
            if "pk__likes" in str(e):
                raise PostAlreadyLikedError("Post already liked") from e
            raise PostRepositoryError(str(e)) from e
        except psycopg.errors.Error as e:
            raise PostRepositoryError(str(e)) from e

    def dislike_post(self, post_id: int, user_id: int) -> None:
        """
        Remove a like from a post for a given user.

        Args:
            post_id (int): ID of the post to unlike.
            user_id (int): ID of the user unliking the post.

        Raises:
            PostRepositoryError: For any unexpected database errors.
        """
        query = """
            DELETE FROM likes
            WHERE post_id = %s AND user_id = %s
        """
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (post_id, user_id))
        except psycopg.errors.Error as e:
            raise PostRepositoryError("Unknown error") from e
