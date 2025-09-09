import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=False)
    
    mode: str = "local"
    port: int = 8000
    db_url: Optional[str] = None
    tiles_path: str = "./data/tiles/risk.pmtiles"
    
    # Data paths
    data_dir: Path = Path("data")
    mock_dir: Path = Path("data/mock")
    tiles_dir: Path = Path("data/tiles")
    config_dir: Path = Path("config")
    
    # API settings
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Tokyo Disaster Anticipation API"
    version: str = "0.1.0"


settings = Settings()