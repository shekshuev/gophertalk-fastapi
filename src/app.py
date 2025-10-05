from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from gophertalk_fastapi.config.config import Config
from gophertalk_fastapi.config.db import create_pool
from gophertalk_fastapi.repository.post_repository import PostRepository
from gophertalk_fastapi.repository.user_repository import UserRepository
from gophertalk_fastapi.routers.auth_router import AuthRouter
from gophertalk_fastapi.service.auth_service import AuthService
from gophertalk_fastapi.service.post_service import PostService
from gophertalk_fastapi.service.user_service import UserService


def create_app() -> FastAPI:
    cfg = Config()
    pool = create_pool(cfg)
    user_repository = UserRepository(pool)
    post_repository = PostRepository(pool)
    auth_service = AuthService(user_repository=user_repository, cfg=cfg)
    _ = PostService(post_repository=post_repository, cfg=cfg)
    _ = UserService(user_repository=user_repository, cfg=cfg)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        pool.close()

    app = FastAPI(title="GopherTalk", lifespan=lifespan)
    auth_router = AuthRouter(auth_service=auth_service)
    app.include_router(auth_router.router)

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
