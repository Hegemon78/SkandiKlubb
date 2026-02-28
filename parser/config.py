"""Parser configuration loader."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from parser/ directory
load_dotenv(Path(__file__).parent / ".env")

DB_PATH = str(Path(__file__).parent.parent / "data" / "chats" / "messages.db")
SESSION_PATH = str(Path(__file__).parent / os.getenv("TELETHON_SESSION_NAME", "skandiklubb_parser"))


@dataclass(frozen=True)
class Config:
    api_id: int
    api_hash: str
    session_name: str
    db_path: str


def load_config() -> Config:
    api_id = os.getenv("TELETHON_API_ID")
    api_hash = os.getenv("TELETHON_API_HASH")

    if not api_id or not api_hash:
        raise ValueError(
            "TELETHON_API_ID and TELETHON_API_HASH must be set in parser/.env\n"
            "Get them at https://my.telegram.org"
        )

    return Config(
        api_id=int(api_id),
        api_hash=api_hash,
        session_name=SESSION_PATH,
        db_path=DB_PATH,
    )
