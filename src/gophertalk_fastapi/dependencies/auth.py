from fastapi import HTTPException, Request
from jose import JWTError, jwt

from ..config.config import Config
from ..models.auth import TokenPayload


def get_current_user(cfg: Config, token_type: str = "access"):
    def dependency(request: Request) -> TokenPayload:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing token")

        token = auth_header[7:]

        try:
            payload = jwt.decode(
                token, cfg.access_token_secret, algorithms=[cfg.hash_algorithm]
            )
            if payload.get("type") != token_type:
                raise HTTPException(status_code=401, detail="Wrong token type")
            user = TokenPayload(**payload)
            request.state.user = user
            return user
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    return dependency
