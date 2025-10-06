from psycopg_pool import ConnectionPool

from .config import Config


def create_pool(cfg: Config) -> ConnectionPool:
    return ConnectionPool(
        conninfo=f"postgresql://{cfg.database_user}:{cfg.database_password}@{cfg.database_host}:{cfg.database_port}/{cfg.database_name}",
        min_size=cfg.database_min_pool_size,
        max_size=cfg.database_max_pool_size,
    )
