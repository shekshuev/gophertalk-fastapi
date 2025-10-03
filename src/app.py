from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from gophertalk_fastapi.config.config import Config
from gophertalk_fastapi.config.db import create_pool
from gophertalk_fastapi.repository.user_repository import UserRepository


def create_app() -> FastAPI:
    cfg = Config()
    pool = create_pool(cfg)
    _ = UserRepository(pool)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        pool.close()

    app = FastAPI(title="GopherTalk", lifespan=lifespan)

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
