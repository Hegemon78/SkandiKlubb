"""List all groups/supergroups the user is a member of.

Run:  python list_chats.py
Shows chat ID, title, members count — use to pick chats for parsing.
"""

import asyncio

from telethon import TelegramClient
from telethon.tl.types import Channel, Chat

from config import load_config


async def main():
    cfg = load_config()
    client = TelegramClient(cfg.session_name, cfg.api_id, cfg.api_hash)
    await client.start()

    print("=== Your Groups & Supergroups ===\n")
    print(f"{'ID':>15}  {'Members':>7}  {'Type':>10}  Title")
    print("-" * 70)

    groups = []
    async for dialog in client.iter_dialogs():
        entity = dialog.entity

        if isinstance(entity, Channel) and entity.megagroup:
            groups.append({
                "id": entity.id,
                "title": dialog.title,
                "members": getattr(entity, "participants_count", None) or "?",
                "type": "supergroup",
                "username": entity.username,
            })
        elif isinstance(entity, Chat):
            groups.append({
                "id": entity.id,
                "title": dialog.title,
                "members": getattr(entity, "participants_count", None) or "?",
                "type": "group",
                "username": None,
            })

    # Sort by members count (descending)
    groups.sort(key=lambda g: g["members"] if isinstance(g["members"], int) else 0, reverse=True)

    for g in groups:
        username = f"  @{g['username']}" if g["username"] else ""
        print(f"{g['id']:>15}  {str(g['members']):>7}  {g['type']:>10}  {g['title']}{username}")

    print(f"\nTotal: {len(groups)} groups")
    print("\nUse chat IDs in chat_parser.py to parse specific groups.")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
