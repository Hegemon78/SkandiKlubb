"""SQLite database layer for parsed Telegram messages."""

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER UNIQUE NOT NULL,
    title TEXT,
    username TEXT,
    members_count INTEGER,
    last_parsed TEXT,
    total_messages INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    sender_id INTEGER,
    sender_name TEXT,
    text TEXT,
    reply_to INTEGER,
    media_type TEXT,
    category TEXT,
    subcategory TEXT,
    processed INTEGER DEFAULT 0,
    confidence REAL DEFAULT 0.5,
    needs_ai_review INTEGER DEFAULT 0,
    UNIQUE(chat_id, message_id)
);

CREATE INDEX IF NOT EXISTS idx_messages_category ON messages(category);
CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(date);
CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_ai_review ON messages(needs_ai_review);
"""

MIGRATION_V2 = [
    "ALTER TABLE messages ADD COLUMN confidence REAL DEFAULT 0.5",
    "ALTER TABLE messages ADD COLUMN needs_ai_review INTEGER DEFAULT 0",
    "CREATE INDEX IF NOT EXISTS idx_messages_ai_review ON messages(needs_ai_review)",
]


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SCHEMA)
        await self._db.commit()
        await self._migrate()

    async def _migrate(self) -> None:
        """Apply schema migrations for existing databases."""
        cursor = await self._db.execute("PRAGMA table_info(messages)")
        columns = {row[1] for row in await cursor.fetchall()}
        if "confidence" not in columns:
            for sql in MIGRATION_V2:
                try:
                    await self._db.execute(sql)
                except aiosqlite.OperationalError:
                    pass  # column/index already exists
            await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    async def upsert_chat(
        self,
        chat_id: int,
        title: str | None = None,
        username: str | None = None,
        members_count: int | None = None,
    ) -> None:
        await self._db.execute(
            """
            INSERT INTO chats (chat_id, title, username, members_count)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                title = COALESCE(excluded.title, title),
                username = COALESCE(excluded.username, username),
                members_count = COALESCE(excluded.members_count, members_count)
            """,
            (chat_id, title, username, members_count),
        )
        await self._db.commit()

    async def update_chat_stats(
        self, chat_id: int, last_parsed: str, total_messages: int
    ) -> None:
        await self._db.execute(
            """
            UPDATE chats
            SET last_parsed = ?, total_messages = ?
            WHERE chat_id = ?
            """,
            (last_parsed, total_messages, chat_id),
        )
        await self._db.commit()

    async def get_last_message_id(self, chat_id: int) -> int | None:
        cursor = await self._db.execute(
            "SELECT MAX(message_id) FROM messages WHERE chat_id = ?",
            (chat_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row and row[0] else None

    async def insert_messages(self, messages: list[dict]) -> int:
        if not messages:
            return 0

        inserted = 0
        for msg in messages:
            try:
                await self._db.execute(
                    """
                    INSERT OR IGNORE INTO messages
                        (chat_id, message_id, date, sender_id, sender_name,
                         text, reply_to, media_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        msg["chat_id"],
                        msg["message_id"],
                        msg["date"],
                        msg.get("sender_id"),
                        msg.get("sender_name"),
                        msg.get("text"),
                        msg.get("reply_to"),
                        msg.get("media_type"),
                    ),
                )
                inserted += 1
            except Exception:
                pass  # skip duplicates silently

        await self._db.commit()
        return inserted

    async def get_message_count(self, chat_id: int | None = None) -> int:
        if chat_id:
            cursor = await self._db.execute(
                "SELECT COUNT(*) FROM messages WHERE chat_id = ?", (chat_id,)
            )
        else:
            cursor = await self._db.execute("SELECT COUNT(*) FROM messages")
        row = await cursor.fetchone()
        return row[0]

    async def get_chats(self) -> list[dict]:
        cursor = await self._db.execute(
            "SELECT chat_id, title, username, members_count, last_parsed, total_messages FROM chats"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
