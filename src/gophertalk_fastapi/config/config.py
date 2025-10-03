import os
from dataclasses import dataclass
from datetime import timedelta


@dataclass
class Config:
    """App config"""

    database_host: str = os.getenv("DATABASE_HOST", "localhost")
    database_port: str = os.getenv("DATABASE_PORT", "5432")
    database_name: str = os.getenv("DATABASE_NAME", "gophertalk")
    database_user: str = os.getenv("DATABASE_USER", "gophertalk")
    database_password: str = os.getenv("DATABASE_PASSWORD", "gophertalk")
    access_token_expires: timedelta = timedelta(
        seconds=int(os.getenv("ACCESS_TOKEN_EXPIRES", 3600))
    )
    refresh_token_expires: timedelta = timedelta(
        seconds=int(os.getenv("REFRESH_TOKEN_EXPIRES", 86400))
    )
    access_token_secret: str = os.getenv("ACCESS_TOKEN_SECRET", "changeme")
    refresh_token_secret: str = os.getenv("REFRESH_TOKEN_SECRET", "changeme")
