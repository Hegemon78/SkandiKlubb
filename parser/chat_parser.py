"""Parse Telegram group chats and save to SQLite.

Usage:
    python chat_parser.py --list              # Show saved chats stats
    python chat_parser.py CHAT_ID [CHAT_ID…]  # Parse specific chats
    python chat_parser.py --all               # Re-parse all saved chats

Supports incremental parsing: only fetches messages newer than last parsed.
"""

import argparse
import asyncio
import logging
import time
from datetime import datetime, timezone

from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User

from config import load_config
from db import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Rate limiting: pause between batches to avoid Telegram limits
BATCH_PAUSE = 1.0  # seconds between every 100 messages


async def parse_chat(
    client: TelegramClient,
    db: Database,
    chat_id: int,
    limit: int | None = None,
) -> dict:
    """Parse a single chat and save messages to DB.

    Args:
        client: Connected Telethon client.
        db: Connected database.
        chat_id: Telegram chat/group ID.
        limit: Max messages to fetch (None = all).

    Returns:
        Stats dict with counts.
    """
    # Get chat entity and metadata
    try:
        entity = await client.get_entity(chat_id)
    except Exception as e:
        logger.error("Cannot access chat %s: %s", chat_id, e)
        return {"error": str(e)}

    title = getattr(entity, "title", str(chat_id))
    username = getattr(entity, "username", None)
    members = getattr(entity, "participants_count", None)

    logger.info("Parsing: %s (ID: %s, members: %s)", title, chat_id, members or "?")

    # Register chat in DB
    await db.upsert_chat(chat_id, title, username, members)

    # Check for incremental parsing
    last_id = await db.get_last_message_id(chat_id)
    if last_id:
        logger.info("Incremental mode: fetching messages after ID %d", last_id)

    messages = []
    total_scanned = 0
    skipped_non_text = 0
    skipped_bots = 0

    async for msg in client.iter_messages(entity, limit=limit):
        total_scanned += 1

        # Incremental: stop if we've reached already-parsed messages
        if last_id and msg.id <= last_id:
            logger.info("Reached last parsed message (ID %d), stopping", last_id)
            break

        # Skip service messages (joins, pins, etc.)
        if msg.action:
            continue

        # Determine media type
        media_type = None
        if msg.photo:
            media_type = "photo"
        elif msg.document:
            media_type = "document"
        elif msg.video:
            media_type = "video"
        elif msg.voice:
            media_type = "voice"
        elif msg.sticker:
            media_type = "sticker"

        # Skip messages with no text and no useful media
        if not msg.text and not media_type:
            skipped_non_text += 1
            continue

        # Get sender info
        sender_name = None
        sender_id = None
        if msg.sender:
            sender_id = msg.sender_id
            if isinstance(msg.sender, User):
                if msg.sender.bot:
                    skipped_bots += 1
                    continue
                sender_name = " ".join(
                    filter(None, [msg.sender.first_name, msg.sender.last_name])
                )
            elif isinstance(msg.sender, (Channel, Chat)):
                sender_name = getattr(msg.sender, "title", None)

        reply_to = None
        if msg.reply_to:
            reply_to = msg.reply_to.reply_to_msg_id

        messages.append({
            "chat_id": chat_id,
            "message_id": msg.id,
            "date": msg.date.strftime("%Y-%m-%d %H:%M:%S"),
            "sender_id": sender_id,
            "sender_name": sender_name,
            "text": msg.text or "",
            "reply_to": reply_to,
            "media_type": media_type,
        })

        # Rate limiting + progress
        if total_scanned % 100 == 0:
            logger.info(
                "  scanned %d messages, collected %d text...",
                total_scanned, len(messages),
            )
            await asyncio.sleep(BATCH_PAUSE)

    # Insert in chronological order
    messages.reverse()
    inserted = await db.insert_messages(messages)

    # Update chat stats
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    total_in_db = await db.get_message_count(chat_id)
    await db.update_chat_stats(chat_id, now, total_in_db)

    stats = {
        "chat": title,
        "scanned": total_scanned,
        "collected": len(messages),
        "inserted": inserted,
        "skipped_non_text": skipped_non_text,
        "skipped_bots": skipped_bots,
        "total_in_db": total_in_db,
    }
    logger.info("Done: %s", stats)
    return stats


async def show_stats(db: Database) -> None:
    """Show stats for all parsed chats."""
    chats = await db.get_chats()
    if not chats:
        print("No chats parsed yet. Run: python chat_parser.py CHAT_ID")
        return

    print(f"\n{'Chat ID':>15}  {'Messages':>8}  {'Last Parsed':>20}  Title")
    print("-" * 75)
    total = 0
    for c in chats:
        total += c["total_messages"] or 0
        print(
            f"{c['chat_id']:>15}  {c['total_messages'] or 0:>8}  "
            f"{c['last_parsed'] or 'never':>20}  {c['title']}"
        )
    print(f"\nTotal messages in DB: {total}")


async def main():
    parser = argparse.ArgumentParser(description="Parse Telegram chats to SQLite")
    parser.add_argument("chats", nargs="*", help="Chat IDs or @usernames to parse")
    parser.add_argument("--list", action="store_true", help="Show parsed chats stats")
    parser.add_argument("--all", action="store_true", help="Re-parse all saved chats")
    parser.add_argument("--limit", type=int, default=None, help="Max messages per chat")
    args = parser.parse_args()

    cfg = load_config()
    db = Database(cfg.db_path)
    await db.connect()

    if args.list:
        await show_stats(db)
        await db.close()
        return

    # Connect Telethon
    client = TelegramClient(cfg.session_name, cfg.api_id, cfg.api_hash)
    await client.start()
    me = await client.get_me()
    logger.info("Connected as @%s", me.username)

    # Determine which chats to parse
    chat_ids = []
    if args.all:
        chats = await db.get_chats()
        chat_ids = [c["chat_id"] for c in chats]
        if not chat_ids:
            print("No saved chats. Specify chat IDs: python chat_parser.py CHAT_ID")
    elif args.chats:
        for c in args.chats:
            # Support both numeric IDs and @usernames
            if c.lstrip("-").isdigit():
                chat_ids.append(int(c))
            else:
                # Resolve username to entity
                try:
                    entity = await client.get_entity(c)
                    chat_ids.append(entity.id)
                    logger.info("Resolved %s -> ID %d", c, entity.id)
                except Exception as e:
                    logger.error("Cannot resolve %s: %s", c, e)
    else:
        parser.print_help()
        await client.disconnect()
        await db.close()
        return

    # Parse each chat
    start = time.time()
    all_stats = []
    for cid in chat_ids:
        stats = await parse_chat(client, db, cid, limit=args.limit)
        all_stats.append(stats)

    elapsed = time.time() - start

    # Summary
    print("\n=== Parsing Complete ===")
    for s in all_stats:
        if "error" in s:
            print(f"  ERROR: {s['error']}")
        else:
            print(
                f"  {s['chat']}: {s['inserted']} new messages "
                f"({s['total_in_db']} total in DB)"
            )
    print(f"\nTime: {elapsed:.1f}s")

    await client.disconnect()
    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
