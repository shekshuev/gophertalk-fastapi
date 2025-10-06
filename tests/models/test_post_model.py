from datetime import timezone, datetime

import pytest
from pydantic import ValidationError

from gophertalk_fastapi.models.post import (
    CreatePostDto,
    FilterPostDto,
    ReadPostDto,
    ReadPostUserDto,
)


def test_create_post_dto_valid():
    """
    Should create a valid `CreatePostDto` instance when all fields are correct.

    This test ensures that required and optional fields of `CreatePostDto`
    pass validation with valid input values.
    """
    dto = CreatePostDto(text="Hello world!", reply_to_id=1, user_id=10)
    assert dto.text == "Hello world!"
    assert dto.reply_to_id == 1
    assert dto.user_id == 10


def test_create_post_dto_empty_text():
    """
    Should raise ValidationError when text is empty.
    """
    with pytest.raises(ValidationError):
        CreatePostDto(text="", user_id=5)


def test_create_post_dto_text_too_long():
    """
    Should raise ValidationError when text exceeds 280 characters.
    """
    with pytest.raises(ValidationError):
        CreatePostDto(text="a" * 281, user_id=1)


def test_create_post_dto_invalid_reply_to_id():
    """
    Should raise ValidationError when `reply_to_id` is below minimum (ge=1).
    """
    with pytest.raises(ValidationError):
        CreatePostDto(text="Hello", reply_to_id=0, user_id=1)


def test_filter_post_dto_valid():
    """
    Should allow optional filters to be set correctly in `FilterPostDto`.
    """
    dto = FilterPostDto(
        search="test",
        owner_id=1,
        user_id=2,
        reply_to_id=3,
        limit=10,
        offset=0,
    )
    assert dto.search == "test"
    assert dto.limit == 10
    assert dto.offset == 0


def test_filter_post_dto_invalid_limit():
    """
    Should raise ValidationError if `limit` is below 1.
    """
    with pytest.raises(ValidationError):
        FilterPostDto(limit=0)


def test_filter_post_dto_invalid_offset():
    """
    Should raise ValidationError if `offset` is negative.
    """
    with pytest.raises(ValidationError):
        FilterPostDto(offset=-1)


def test_read_post_user_dto_valid():
    """
    Should correctly instantiate a `ReadPostUserDto`.
    """
    user = ReadPostUserDto(
        id=1, user_name="alice", first_name="Alice", last_name="Smith"
    )
    assert user.id == 1
    assert user.user_name == "alice"
    assert user.first_name == "Alice"


def test_read_post_dto_valid_with_nested_user():
    """
    Should allow nested `ReadPostUserDto` inside `ReadPostDto`.
    """
    user = ReadPostUserDto(id=1, user_name="john", first_name="John", last_name="Doe")
    dto = ReadPostDto(
        id=1,
        text="Hello!",
        user_id=42,
        reply_to_id=None,
        created_at=datetime.now(timezone.utc),
        likes_count=5,
        views_count=100,
        user=user,
    )
    assert dto.user.user_name == "john"
    assert dto.likes_count == 5
    assert dto.views_count == 100


def test_read_post_dto_missing_required_field():
    """
    Should raise ValidationError if required fields are missing.
    """
    with pytest.raises(ValidationError):
        ReadPostDto(
            id=1,
            text=None,
            user_id=42,
            reply_to_id=None,
            created_at=datetime.now(timezone.utc),
        )
