"""Keyword-based categorization of parsed Telegram messages.

Usage:
    python data_processor.py              # Categorize all uncategorized messages
    python data_processor.py --reset      # Reset categories, re-process all
    python data_processor.py --stats      # Show category distribution
    python data_processor.py --sample N   # Show N random samples per category
"""

import argparse
import re
import sqlite3
import time

from config import load_config

# ---------------------------------------------------------------------------
# Subcategory rules: topic detection by keywords
# Order matters — first match wins within a category
# ---------------------------------------------------------------------------

SUBCATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("parking", [
        r"паркинг", r"кладов[аоыкуе]", r"затоп\w*кладов", r"подземн\w+парк",
        r"машиноместо", r"паркоместо", r"въезд\w*парк", r"выезд\w*парк",
    ]),
    ("skud", [
        r"ворота", r"калитк", r"домофон", r"[сc][кk][уy][дd]",
        r"ключ\w*доступ", r"брелок", r"интерком", r"шлагбаум",
        r"кодов\w+замо[кч]", r"магнитн\w+замо[кч]",
    ]),
    ("elevator", [
        r"лифт",
    ]),
    ("water", [
        r"горяч\w+вод", r"холодн\w+вод", r"отоплен", r"батаре[йяюе]",
        r"труб[аыуе]", r"полотенцесушител", r"радиатор",
        r"теплоснабжен", r"проток\w+нагревател",
    ]),
    ("electricity", [
        r"электричеств", r"розетк", r"автомат\w+выбива", r"щиток",
        r"освещен\w+парадн", r"электрик", r"напряжен\w+сети",
    ]),
    ("repair", [
        r"фасад", r"кондиционер", r"остеклен", r"балкон",
        r"штукатурк", r"трещин\w+стен", r"плитк\w+отвалил",
        r"козырь?[её]к", r"отмостк",
    ]),
    ("territory", [
        r"двор\w*(?:овая|у|ы|е|а)?", r"парковк[аиуе]",
        r"мусор", r"снег", r"убор[кч]",
        r"детск\w+площадк", r"газон", r"озеленен", r"благоустройств",
        r"пухто", r"контейнер\w+мусор",
    ]),
    ("cameras", [
        r"камер\w+наблюден", r"видеонаблюден", r"камер\w+(?:не\s*)?работа",
        r"запис\w+камер",
    ]),
    ("security", [
        r"охран[аеуик]", r"безопасност", r"краж", r"воровств",
        r"посторонн\w+(?:лиц|люд)", r"проник\w+(?:в|на)",
        r"консьерж", r"пост\w*охран",
    ]),
    ("uk", [
        r"эквид", r"управляш", r"управляющ\w+компан",
        r"не\s*отвеча[юе]т", r"диспетчер",
        r"(?:наша|эта)\s+ук", r"[уy][кk]\s+(?:не|всегда|опять|сново)",
    ]),
    ("oss", [
        r"[оo][сc][сc]", r"собран\w+собственник", r"голосован",
        r"повестк", r"кворум", r"бюллетен", r"инициатив\w+групп",
        r"счётн\w+комисс",
    ]),
    ("fees", [
        r"капремонт", r"взнос\w*(?:за|на)", r"[фf][кk][рp]",
        r"тариф", r"перерасч[ёе]т", r"квитанц", r"начислен",
        r"(?:платёж|оплат)\w*(?:за|жкх|ку)", r"задолженност",
    ]),
    ("ventilation", [
        r"рекупер", r"вентиляц", r"приточн", r"co2", r"углекисл",
        r"фильтр\w*рекупер", r"бризер",
    ]),
]

# ---------------------------------------------------------------------------
# Category rules: what type of message is this?
# Priority: contact > ad > info > solution > problem > faq > other
# ---------------------------------------------------------------------------

# Regex patterns for each category
CONTACT_PATTERNS = [
    r"\+7[\s\-\(]?\d{3}[\s\-\)]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}",
    r"\+7\d{10}",
    r"8[\s\-\(]?\d{3}[\s\-\)]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}",
    r"(?:телефон|контакт|номер)\w*\s*[:—–-]\s*\+?\d",
    r"(?:звоните|обращайтесь)\s*(?:по|на)?\s*[:—–-]?\s*\+?\d",
]

AD_PATTERNS = [
    r"(?:предлагаю|предлагаем|оказываю|оказываем)\s+услуг",
    r"ремонт\s+(?:под\s+ключ|квартир|балкон|ванн)",
    r"(?:прайс|расценк|стоимость\s+услуг)",
    r"(?:заказ|оформить|оставить\s+заявк)\w*\s*(?:по|на|у|в)",
    r"(?:скидк\w+|акци[яю]|промокод)\s+\d",
    r"(?:дизайн|монтаж|установк)\w*\s+(?:под|от|за)\s+\d",
]

INFO_PATTERNS = [
    r"уважаемые\s+жител",
    r"информируем",
    r"(?:завтра|сегодня)\s+(?:с\s+\d|в\s+\d|будет\s+(?:проводи|осуществля|отключ|включ))",
    r"плановые?\s+(?:работ|отключен|ремонт)",
    r"просим\s+(?:вас|обратить|не\s+парковать|использовать)",
    r"(?:ремонтные|профилактические)\s+работы\s+(?:завершен|начат|проводятся)",
]

SOLUTION_PATTERNS = [
    r"(?:починил|отремонтировал|исправил|устранил|решил)\w*",
    r"(?:заработал|включил|восстановил|запустил)\w*\s+(?:обратно|снова)?",
    r"(?:мне|нам)\s+помогло",
    r"работы\s+(?:завершены|выполнены)",
    r"(?:проблем\w+\s+)?(?:реш[иеё]н|устранен)",
    r"(?:скамейк|ворот|лифт|камер)\w*\s+(?:починил|отремонтировал|заработал)",
]

PROBLEM_PATTERNS = [
    r"не\s+работа[ею]т",
    r"(?:сломал|поломал|вышл\w+из\s+строя|неисправн)\w*",
    r"(?:протечк|затопил|течёт|течет|льётся|подтекает)\w*",
    r"(?:когда\s+)?(?:починят|отремонтируют|исправят|устранят)",
    r"(?:жалоб|претенз|обращен)\w+\s+(?:в|на|к)",
    r"(?:опять|снова|опять\s+не|снова\s+не)\s+\w+",
    r"(?:нараспашку|открыты\s+настежь)",
    r"(?:проблем\w+\s+с|перебо\w+\s+с)",
    r"(?:бездейств|игнорир|не\s+реагир)\w*",
]

FAQ_PATTERNS = [
    r"(?:подскажите|посоветуйте|порекомендуйте)\b",
    r"(?:у\s+кого|кто[\s-]+нибудь|кто\s+знает|кто\s+сталкивался)\b",
    r"(?:как\s+(?:правильно|лучше|можно|вы)\s+\w+)\?",
    r"(?:где\s+(?:можно|лучше|находит|искать))\b",
    r"(?:какой|какую|каких)\s+\w+\s+(?:ставите|используете|выбрали|рекомендуете)",
    r"(?:есть\s+(?:у\s+кого|ли)\s+\w+)\?",
]


def detect_subcategory(text: str) -> str | None:
    """Detect topic/subcategory from text."""
    text_lower = text.lower()
    for subcat, patterns in SUBCATEGORY_RULES:
        for pat in patterns:
            if re.search(pat, text_lower):
                return subcat
    return None


def categorize_message(text: str, chat_id: int) -> tuple[str, str | None]:
    """Categorize a single message.

    Returns:
        (category, subcategory) tuple.
    """
    if not text or not text.strip():
        return ("other", None)

    # Short messages (< 15 chars) — almost always noise
    if len(text.strip()) < 15:
        # Unless it contains a phone number
        for pat in CONTACT_PATTERNS:
            if re.search(pat, text):
                return ("contact", None)
        return ("other", None)

    # UK channel (2081187522) — mostly info announcements
    if chat_id == 2081187522:
        subcat = detect_subcategory(text)
        # Check if it's a solution (repair completed)
        for pat in SOLUTION_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                return ("solution", subcat)
        return ("info", subcat)

    text_lower = text.lower()

    # 1. Contact — phone numbers, contact sharing
    for pat in CONTACT_PATTERNS:
        if re.search(pat, text):
            subcat = detect_subcategory(text)
            return ("contact", subcat)

    # 2. Ad — service offers
    for pat in AD_PATTERNS:
        if re.search(pat, text_lower):
            return ("ad", detect_subcategory(text))

    # 3. Info — official announcements (from forwarded UK messages)
    for pat in INFO_PATTERNS:
        if re.search(pat, text_lower):
            return ("info", detect_subcategory(text))

    # 4. Solution — something was fixed
    for pat in SOLUTION_PATTERNS:
        if re.search(pat, text_lower):
            return ("solution", detect_subcategory(text))

    # 5. Problem — complaints, broken things
    for pat in PROBLEM_PATTERNS:
        if re.search(pat, text_lower):
            return ("problem", detect_subcategory(text))

    # 6. FAQ — questions, advice seeking
    for pat in FAQ_PATTERNS:
        if re.search(pat, text_lower):
            return ("faq", detect_subcategory(text))

    # 7. Topic-only (has subcategory but no clear category)
    subcat = detect_subcategory(text)
    if subcat:
        # Has a topic but unclear sentiment — mark for AI review later
        return ("topic", subcat)

    return ("other", None)


def process_all(db_path: str, reset: bool = False) -> dict:
    """Process all messages in the database.

    Args:
        db_path: Path to SQLite database.
        reset: If True, reset all categories before processing.

    Returns:
        Stats dict with category counts.
    """
    db = sqlite3.connect(db_path)

    if reset:
        db.execute("UPDATE messages SET category = NULL, subcategory = NULL, processed = 0")
        db.commit()
        print("Reset all categories.")

    # Get uncategorized messages
    rows = db.execute(
        "SELECT id, chat_id, text FROM messages WHERE category IS NULL"
    ).fetchall()

    if not rows:
        print("All messages already categorized. Use --reset to re-process.")
        return {}

    print(f"Processing {len(rows)} messages...")
    start = time.time()

    stats: dict[str, int] = {}
    batch = []

    for i, (msg_id, chat_id, text) in enumerate(rows):
        category, subcategory = categorize_message(text or "", chat_id)

        batch.append((category, subcategory, msg_id))
        stats[category] = stats.get(category, 0) + 1

        if len(batch) >= 1000:
            db.executemany(
                "UPDATE messages SET category = ?, subcategory = ?, processed = 1 WHERE id = ?",
                batch,
            )
            db.commit()
            batch.clear()
            print(f"  processed {i + 1}/{len(rows)}...")

    # Flush remaining
    if batch:
        db.executemany(
            "UPDATE messages SET category = ?, subcategory = ?, processed = 1 WHERE id = ?",
            batch,
        )
        db.commit()

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.1f}s")

    db.close()
    return stats


def show_stats(db_path: str) -> None:
    """Show category distribution."""
    db = sqlite3.connect(db_path)

    print("\n=== КАТЕГОРИИ ===")
    total = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    rows = db.execute(
        "SELECT category, COUNT(*) as cnt FROM messages GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    for cat, cnt in rows:
        pct = cnt * 100 / total
        bar = "#" * int(pct)
        print(f"  {cat or 'NULL':<12} {cnt:>6}  ({pct:>5.1f}%)  {bar}")

    print(f"\n  Total: {total}")

    print("\n=== ПОДКАТЕГОРИИ (топ-20) ===")
    rows = db.execute(
        """SELECT subcategory, category, COUNT(*) as cnt FROM messages
           WHERE subcategory IS NOT NULL
           GROUP BY subcategory ORDER BY cnt DESC LIMIT 20"""
    ).fetchall()
    for subcat, cat, cnt in rows:
        print(f"  {subcat:<15} ({cat:<8}) {cnt:>5}")

    print("\n=== ПОДКАТЕГОРИИ ПРОБЛЕМ ===")
    rows = db.execute(
        """SELECT subcategory, COUNT(*) as cnt FROM messages
           WHERE category = 'problem' AND subcategory IS NOT NULL
           GROUP BY subcategory ORDER BY cnt DESC"""
    ).fetchall()
    for subcat, cnt in rows:
        bar = "#" * (cnt // 10)
        print(f"  {subcat:<15} {cnt:>5}  {bar}")

    db.close()


def show_samples(db_path: str, n: int) -> None:
    """Show random samples for each category."""
    db = sqlite3.connect(db_path)

    categories = [r[0] for r in db.execute(
        "SELECT DISTINCT category FROM messages WHERE category IS NOT NULL ORDER BY category"
    ).fetchall()]

    for cat in categories:
        print(f"\n{'=' * 60}")
        print(f"  CATEGORY: {cat}")
        print(f"{'=' * 60}")
        rows = db.execute(
            "SELECT sender_name, substr(text, 1, 200) FROM messages "
            "WHERE category = ? AND length(text) > 20 ORDER BY RANDOM() LIMIT ?",
            (cat, n),
        ).fetchall()
        for name, text in rows:
            print(f"  [{name}] {text}")
            print()

    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Categorize parsed messages")
    parser.add_argument("--reset", action="store_true", help="Reset all categories")
    parser.add_argument("--stats", action="store_true", help="Show category stats")
    parser.add_argument("--sample", type=int, default=0, help="Show N samples per category")
    args = parser.parse_args()

    cfg = load_config()

    if args.stats:
        show_stats(cfg.db_path)
    elif args.sample:
        show_samples(cfg.db_path, args.sample)
    else:
        stats = process_all(cfg.db_path, reset=args.reset)
        if stats:
            print("\nDistribution:")
            for cat, cnt in sorted(stats.items(), key=lambda x: -x[1]):
                print(f"  {cat:<12} {cnt:>6}")
            print("\nRun --stats for detailed breakdown, --sample 5 for examples.")
