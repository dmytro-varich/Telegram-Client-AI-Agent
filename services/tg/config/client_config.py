from anyio import Path
from dataclasses import dataclass

@dataclass
class BaseTelegramConfig:
    api_id: int
    api_hash: str
    phone: str | None = None

    
@dataclass
class TDLibConfig(BaseTelegramConfig):
    db_enc_key: str | bytes = "db_key"
    library_path: str | None = None
    files_directory: str | Path | None = None
    name: str | None = None
    tdlib_verbosity: int = 2