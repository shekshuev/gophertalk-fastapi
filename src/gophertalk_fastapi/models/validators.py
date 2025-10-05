import re


def username_validator(value: str) -> str:
    if not re.match(r"^[a-zA-Z0-9_]{5,30}$", value):
        raise ValueError("Must be alphanumeric or underscore (5-30 characters)")
    if re.match(r"^[0-9]", value):
        raise ValueError("Must start with a letter")
    return value


def password_validator(value: str) -> str:
    if not re.match(r"^(?=.*[a-zA-Z])(?=.*\d)(?=.*[@$!%*?&]).{5,30}$", value):
        raise ValueError(
            "Must contain letter, number and special character (5-30 characters)"
        )
    return value


def name_validator(value: str) -> str:
    if not value.isalpha():
        raise ValueError("Only letters allowed")
    return value
