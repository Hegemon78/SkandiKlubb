"""One-time Telethon authorization.

Run once:  python auth.py
Telegram will send a code to the phone.
After auth, session file is saved and reused.
"""

import asyncio

from telethon import TelegramClient

from config import load_config


async def main():
    cfg = load_config()

    print("=== Telethon Authorization (SkandiKlubb Parser) ===")
    print(f"Session: {cfg.session_name}")
    print(f"API ID:  {cfg.api_id}")
    print()

    client = TelegramClient(cfg.session_name, cfg.api_id, cfg.api_hash)
    await client.start()

    me = await client.get_me()
    print(f"\nAuthorized as: {me.first_name} (@{me.username})")
    print(f"Session saved: {cfg.session_name}.session")
    print("\nReady to parse! Run: python chat_parser.py --list")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
