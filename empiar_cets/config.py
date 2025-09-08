from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

env_file = Path(__file__).parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_file, extra="allow")

    cache_root_dirpath: Path = Path.home() / ".cache" / "cets-empiar"


settings = Settings()
