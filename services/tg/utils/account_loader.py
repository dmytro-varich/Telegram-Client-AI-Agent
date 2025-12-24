import os
from anyio import Path 
from dotenv import dotenv_values

from services.tg.config import TDLibConfig

# Global counter for account names
_account_counter = 1

def require(env: dict, key: str) -> str:
    value = env.get(key)
    if not value:
        raise ValueError(f"Missing required env variable: {key}")
    return value

def load_tdlib_account(
    env_file: str = ".env",
    name: str | None = None,
    *, 
    library_path: str | None = None,
    files_directory: str | Path | None = None,
    tdlib_verbosity: int = 2,
) -> TDLibConfig:
    env = dotenv_values(env_file)
    
    if not name:
        global _account_counter
        name = f"account{_account_counter}"
        _account_counter += 1
    
    if files_directory is None:
        files_directory = str(Path("accounts_data") / name)
    else:
        files_directory = str(files_directory)
        
    return TDLibConfig(
        api_id=int(require(env, "API_ID")),
        api_hash=require(env, "API_HASH"),
        phone=require(env, "PHONE_NUMBER"),
        db_enc_key=require(env, "DB_ENC_KEY"),
        library_path=library_path,
        files_directory=files_directory,
        tdlib_verbosity=tdlib_verbosity,
        name=name,
    )