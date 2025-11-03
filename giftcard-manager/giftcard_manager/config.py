from functools import lru_cache
from pathlib import Path

from platformdirs import PlatformDirs
from pydantic_settings import BaseSettings


def _default_database_url() -> str:
    dirs = PlatformDirs(appname="GiftCardManager", appauthor="YourBusiness")
    base_path = Path(dirs.user_data_dir)
    base_path.mkdir(parents=True, exist_ok=True)
    db_path = base_path / "giftcards.db"
    return f"sqlite:///{db_path}"


class Settings(BaseSettings):
    database_url: str = _default_database_url()

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
