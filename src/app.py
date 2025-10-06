from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Response, status

from gophertalk_fastapi.config.config import Config
from gophertalk_fastapi.config.db import create_pool
from gophertalk_fastapi.repository.post_repository import PostRepository
from gophertalk_fastapi.repository.user_repository import UserRepository
from gophertalk_fastapi.routers.auth_router import AuthRouter
from gophertalk_fastapi.routers.post_router import PostRouter
from gophertalk_fastapi.routers.user_router import UserRouter
from gophertalk_fastapi.service.auth_service import AuthService
from gophertalk_fastapi.service.post_service import PostService
from gophertalk_fastapi.service.user_service import UserService


def create_app() -> FastAPI:
    cfg = Config()
    pool = create_pool(cfg)
    user_repository = UserRepository(pool)
    post_repository = PostRepository(pool)
    auth_service = AuthService(user_repository=user_repository, cfg=cfg)
    post_service = PostService(post_repository=post_repository, cfg=cfg)
    user_service = UserService(user_repository=user_repository, cfg=cfg)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        pool.close()

    app = FastAPI(title="GopherTalk", lifespan=lifespan)
    auth_router = AuthRouter(auth_service=auth_service)
    user_router = UserRouter(user_service=user_service)
    post_router = PostRouter(post_service=post_service, cfg=cfg)
    app.include_router(auth_router.router, prefix="/api")
    app.include_router(user_router.router, prefix="/api")
    app.include_router(post_router.router, prefix="/api")

    @app.get("/api/health-check")
    def health_check():
        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return Response(content="OK", status_code=status.HTTP_200_OK)
        except Exception:
            return Response(
                content="DB connection failed",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
