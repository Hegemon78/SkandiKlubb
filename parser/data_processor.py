"""Weighted-scoring categorization of parsed Telegram messages.

Replaces first-match with scoring: each pattern has a weight, negative
patterns reduce score, confidence = max / (max + second + 1).

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
        r"ворота", r"калитк", r"[сc][кk][уy][дd]",
        r"ключ\w*доступ", r"брелок", r"шлагбаум",
        r"кодов\w+замо[кч]", r"магнитн\w+замо[кч]",
    ]),
    ("intercom", [
        r"домофон", r"интерком", r"трубк\w+домофон", r"домофон\w+не\s",
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
        r"электрик", r"напряжен\w+сети",
    ]),
    ("lighting", [
        r"освещен", r"фонар", r"светильник", r"лампочк",
        r"темно\s+в\s+парадн", r"свет\w*\s+(?:в\s+)?парадн",
        r"свет\w*\s+во\s+двор", r"не\s+гор\w+свет",
    ]),
    ("cleaning", [
        r"убор\w+парадн", r"мыть\w+окн", r"помыть\w+окн", r"грязь\s+в\s+парадн",
        r"грязн\w+парадн", r"не\s+убира", r"уборщиц", r"клининг",
        r"мыли\s+(?:парадн|подъезд)", r"помыли\s+(?:парадн|подъезд)",
    ]),
    ("noise", [
        r"шум\w*\s+(?:от|из|на|в)", r"громк\w+музык", r"стройк\w+шум",
        r"сверл\w+(?:ночь|вечер|утр|выходн)", r"шумн\w+сосед",
        r"шумят", r"шум\w+работ",
    ]),
    ("insects", [
        r"таракан", r"клоп", r"дезинсекц", r"дезинфекц",
        r"травить\w*\s+таракан", r"муравь", r"насеком",
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
# Weighted category patterns: (regex, weight)
# Score = sum of matched pattern weights - negative penalty
# Winner = category with max score
# ---------------------------------------------------------------------------

CATEGORY_PATTERNS: dict[str, list[tuple[str, int]]] = {
    "contact": [
        (r"\+7[\s\-\(]?\d{3}[\s\-\)]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", 10),
        (r"\+7\d{10}", 10),
        (r"8[\s\-\(]?\d{3}[\s\-\)]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", 8),
        (r"(?:телефон|контакт|номер)\w*\s*[:—–-]\s*\+?\d", 8),
        (r"(?:звоните|обращайтесь)\s*(?:по|на)?\s*[:—–-]?\s*\+?\d", 7),
    ],
    "ad": [
        (r"(?:предлагаю|предлагаем|оказываю|оказываем)\s+услуг", 6),
        (r"ремонт\s+(?:под\s+ключ|квартир|балкон|ванн)", 5),
        (r"(?:прайс|расценк|стоимость\s+услуг)", 6),
        (r"(?:заказ|оформить|оставить\s+заявк)\w*\s*(?:по|на|у|в)", 4),
        (r"(?:скидк\w+|акци[яю]|промокод)\s+\d", 6),
        (r"(?:дизайн|монтаж|установк)\w*\s+(?:под|от|за)\s+\d", 5),
        (r"(?:пишите|звоните)\s+(?:в\s+лс|в\s+личк|мне)", 4),
        (r"(?:наша\s+компания|наша\s+фирма|мы\s+занимаемся)", 5),
    ],
    "info": [
        (r"уважаемые\s+жител", 7),
        (r"информируем", 6),
        (r"(?:завтра|сегодня)\s+(?:с\s+\d|в\s+\d|будет\s+(?:проводи|осуществля|отключ|включ))", 5),
        (r"плановые?\s+(?:работ|отключен|ремонт)", 6),
        (r"просим\s+(?:вас|обратить|не\s+парковать|использовать)", 5),
        (r"(?:ремонтные|профилактические)\s+работы\s+(?:завершен|начат|проводятся)", 6),
    ],
    "solution": [
        (r"(?:починил|отремонтировал|исправил|устранил)\w*", 5),
        (r"(?:заработал|включил|восстановил|запустил)\w*\s+(?:обратно|снова)?", 5),
        (r"(?:мне|нам)\s+помогло", 5),
        (r"работы\s+(?:завершены|выполнены)", 6),
        (r"(?:проблем\w+\s+)?(?:реш[её]н[аоы]?\b|устранен)", 5),
        (r"(?:скамейк|ворот|лифт|камер)\w*\s+(?:починил|отремонтировал|заработал)", 7),
    ],
    "problem": [
        (r"не\s+работа[ею]т", 5),
        (r"(?:сломал|поломал|вышл\w+из\s+строя|неисправн)\w*", 6),
        (r"(?:протечк|затопил|течёт|течет|льётся|подтекает)\w*", 6),
        (r"(?:когда\s+)?(?:починят|отремонтируют|исправят|устранят)", 5),
        (r"(?:жалоб|претенз|обращен)\w+\s+(?:в|на|к)", 5),
        (r"(?:опять|снова)\s+не\s+\w+", 5),
        (r"(?:нараспашку|открыты\s+настежь)", 5),
        (r"(?:проблем\w+\s+с|перебо\w+\s+с)", 5),
        (r"(?:бездейств|игнорир|не\s+реагир)\w*", 5),
        # New patterns — catch from OTHER
        (r"темно\s+(?:в|на|у)", 4),
        (r"(?:грязь|грязно)\s+(?:в|на|у)", 4),
        (r"(?:воняет|вонь|запах\w*)\s+(?:в|на|из)", 4),
        (r"таракан\w*\s+(?:в|на|у|опять|снова)", 4),
        (r"не\s+убира[юе]т", 5),
        (r"(?:разбит|разбили|разбилось)\w*", 4),
        (r"(?:засорил|забил)\w*\s+(?:канализац|труб|слив)", 5),
    ],
    "faq": [
        (r"(?:подскажите|посоветуйте|порекомендуйте)\b", 5),
        (r"(?:у\s+кого|кто[\s-]+нибудь|кто\s+знает|кто\s+сталкивался)\b", 5),
        (r"(?:как\s+(?:правильно|лучше|можно|вы)\s+\w+)\?", 5),
        (r"(?:где\s+(?:можно|лучше|находит|искать))\b", 4),
        (r"(?:какой|какую|каких)\s+\w+\s+(?:ставите|используете|выбрали|рекомендуете)", 5),
        (r"(?:есть\s+(?:у\s+кого|ли)\s+\w+)\?", 4),
        # New patterns — catch from OTHER
        (r"(?:а\s+как|а\s+что|а\s+где|а\s+кто)\b", 3),
        (r"(?:кто\s+делал|кто\s+ставил|кто\s+менял)\b", 4),
        (r"(?:кто\s+(?:вам|вы)\s+\w+)\?", 3),
        (r"(?:чем\s+лучше|что\s+лучше)\b", 4),
    ],
}

# ---------------------------------------------------------------------------
# Negative patterns — reduce category score
# ---------------------------------------------------------------------------

NEGATIVE_PATTERNS: dict[str, list[tuple[str, int]]] = {
    "ad": [
        (r"\?", 4),                                   # questions are not ads
        (r"(?:кто[\s-]+нибудь|у\s+кого)\b", 5),      # seeking advice, not selling
        (r"(?:подскажите|посоветуйте)\b", 5),
        (r"(?:где\s+(?:можно|лучше|заказ))\b", 4),   # asking where, not offering
        (r"(?:какой|какую)\s+\w+\s+(?:выбрали|используете)", 4),
    ],
    "solution": [
        (r"\?", 5),                                   # question, not a statement
        (r"решение\s+(?:осс|собран|общего)", 6),      # "решение ОСС" != fix
        (r"(?:осс|собран\w+собственник).{0,60}решен", 6),  # ОСС...решение nearby
        (r"решен\w*.{0,60}(?:осс|собран\w+собственник)", 6),  # решение...ОСС nearby
        (r"голосован\w+\s+(?:за|против)", 5),
        (r"(?:я\s+)?решил\w*\s+(?:не\s+|что\s+)", 5),  # "решил не смотреть"
        (r"(?:принял|вынес)\w*\s+решен", 5),            # formal decision, not fix
        (r"решение\s+(?:оставляет|принять|вопрос)", 5),  # formal "decision"
    ],
    "problem": [
        # standalone "опять/снова" without problem-keyword nearby
        (r"^(?:опять|снова)\s+(?!не\s)(?!слома)(?!протеч)(?!затоп)(?!поломк)"
         r"(?!течёт)(?!течет)(?!забил)(?!засор)(?!воня)(?!грязн)", 4),
    ],
}

# ---------------------------------------------------------------------------
# Question detection — bonus/penalty
# ---------------------------------------------------------------------------

_QUESTION_START = re.compile(
    r"^(?:как|где|кто|почему|что|когда|зачем|куда|откуда|сколько|чем|какой|какая|какие)\b",
    re.IGNORECASE,
)


def _is_question(text: str) -> bool:
    """Check if text is a question."""
    stripped = text.strip()
    if "?" in stripped:
        return True
    if _QUESTION_START.search(stripped):
        return True
    return False


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def detect_subcategory(text: str) -> str | None:
    """Detect topic/subcategory from text."""
    text_lower = text.lower()
    for subcat, patterns in SUBCATEGORY_RULES:
        for pat in patterns:
            if re.search(pat, text_lower):
                return subcat
    return None


def categorize_message(
    text: str, chat_id: int,
) -> tuple[str, str | None, float, bool]:
    """Categorize a single message using weighted scoring.

    Returns:
        (category, subcategory, confidence, needs_ai_review) tuple.
    """
    if not text or not text.strip():
        return ("other", None, 1.0, False)

    # Short messages (< 15 chars) — almost always noise
    if len(text.strip()) < 15:
        for pat, _ in CATEGORY_PATTERNS["contact"]:
            if re.search(pat, text):
                return ("contact", None, 0.9, False)
        return ("other", None, 1.0, False)

    # UK channel (2081187522) — mostly info announcements
    if chat_id == 2081187522:
        subcat = detect_subcategory(text)
        # Check if it's a solution (repair completed)
        sol_score = 0
        text_lower = text.lower()
        for pat, weight in CATEGORY_PATTERNS.get("solution", []):
            if re.search(pat, text_lower):
                sol_score += weight
        # Apply solution negatives
        for pat, penalty in NEGATIVE_PATTERNS.get("solution", []):
            if re.search(pat, text_lower):
                sol_score -= penalty
        if sol_score > 3:
            return ("solution", subcat, 0.85, False)
        return ("info", subcat, 0.9, False)

    text_lower = text.lower()
    is_q = _is_question(text)

    # Compute scores for all categories
    scores: dict[str, float] = {}
    for cat, patterns in CATEGORY_PATTERNS.items():
        score = 0.0
        for pat, weight in patterns:
            if re.search(pat, text_lower):
                score += weight
        # Apply negative patterns
        for neg_pat, penalty in NEGATIVE_PATTERNS.get(cat, []):
            if re.search(neg_pat, text_lower):
                score -= penalty
        scores[cat] = score

    # Question detection bonus/penalty
    if is_q:
        scores["faq"] = scores.get("faq", 0) + 3
        scores["ad"] = scores.get("ad", 0) - 3
        scores["solution"] = scores.get("solution", 0) - 3

    # Clamp negatives to 0
    for cat in scores:
        if scores[cat] < 0:
            scores[cat] = 0

    # Find winner
    sorted_cats = sorted(scores.items(), key=lambda x: -x[1])
    max_score = sorted_cats[0][1] if sorted_cats else 0
    second_score = sorted_cats[1][1] if len(sorted_cats) > 1 else 0

    # Category with highest positive score wins
    if max_score > 0:
        winner = sorted_cats[0][0]
        subcat = detect_subcategory(text)
        confidence = max_score / (max_score + second_score + 1)
        needs_review = confidence < 0.6
        return (winner, subcat, round(confidence, 2), needs_review)

    # Fallback: topic-only (has subcategory but no clear category)
    subcat = detect_subcategory(text)
    if subcat:
        return ("topic", subcat, 0.3, True)

    return ("other", None, 1.0, False)


# ---------------------------------------------------------------------------
# DB processing
# ---------------------------------------------------------------------------

def _migrate_db(db: sqlite3.Connection) -> None:
    """Add confidence/needs_ai_review columns if missing."""
    cols = {r[1] for r in db.execute("PRAGMA table_info(messages)").fetchall()}
    if "confidence" not in cols:
        for sql in [
            "ALTER TABLE messages ADD COLUMN confidence REAL DEFAULT 0.5",
            "ALTER TABLE messages ADD COLUMN needs_ai_review INTEGER DEFAULT 0",
        ]:
            try:
                db.execute(sql)
            except sqlite3.OperationalError:
                pass  # already exists
        db.commit()


def process_all(db_path: str, reset: bool = False) -> dict:
    """Process all messages in the database.

    Args:
        db_path: Path to SQLite database.
        reset: If True, reset all categories before processing.

    Returns:
        Stats dict with category counts.
    """
    db = sqlite3.connect(db_path)
    _migrate_db(db)

    if reset:
        db.execute(
            "UPDATE messages SET category = NULL, subcategory = NULL, "
            "processed = 0, confidence = 0.5, needs_ai_review = 0"
        )
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
        category, subcategory, confidence, needs_review = categorize_message(
            text or "", chat_id,
        )

        batch.append((category, subcategory, confidence, int(needs_review), msg_id))
        stats[category] = stats.get(category, 0) + 1

        if len(batch) >= 1000:
            db.executemany(
                "UPDATE messages SET category = ?, subcategory = ?, "
                "confidence = ?, needs_ai_review = ?, processed = 1 "
                "WHERE id = ?",
                batch,
            )
            db.commit()
            batch.clear()
            print(f"  processed {i + 1}/{len(rows)}...")

    # Flush remaining
    if batch:
        db.executemany(
            "UPDATE messages SET category = ?, subcategory = ?, "
            "confidence = ?, needs_ai_review = ?, processed = 1 "
            "WHERE id = ?",
            batch,
        )
        db.commit()

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.1f}s")

    db.close()
    return stats


def show_stats(db_path: str) -> None:
    """Show category distribution with confidence metrics."""
    db = sqlite3.connect(db_path)
    _migrate_db(db)

    print("\n=== КАТЕГОРИИ ===")
    total = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    if total == 0:
        print("  No messages in database.")
        db.close()
        return
    rows = db.execute(
        "SELECT category, COUNT(*) as cnt, ROUND(AVG(confidence), 2) as avg_conf "
        "FROM messages GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    for cat, cnt, avg_conf in rows:
        pct = cnt * 100 / total
        bar = "#" * int(pct)
        print(f"  {cat or 'NULL':<12} {cnt:>6}  ({pct:>5.1f}%)  conf={avg_conf}  {bar}")

    print(f"\n  Total: {total}")

    # AI review stats
    review_count = db.execute(
        "SELECT COUNT(*) FROM messages WHERE needs_ai_review = 1"
    ).fetchone()[0]
    print(f"\n  Needs AI review: {review_count} ({review_count * 100 / total:.1f}%)")

    review_by_cat = db.execute(
        "SELECT category, COUNT(*) as cnt FROM messages "
        "WHERE needs_ai_review = 1 GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    if review_by_cat:
        print("  By category:")
        for cat, cnt in review_by_cat:
            print(f"    {cat:<12} {cnt:>5}")

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
    """Show random samples for each category with confidence."""
    db = sqlite3.connect(db_path)
    _migrate_db(db)

    categories = [r[0] for r in db.execute(
        "SELECT DISTINCT category FROM messages "
        "WHERE category IS NOT NULL ORDER BY category"
    ).fetchall()]

    for cat in categories:
        print(f"\n{'=' * 60}")
        print(f"  CATEGORY: {cat}")
        print(f"{'=' * 60}")
        rows = db.execute(
            "SELECT sender_name, substr(text, 1, 200), confidence, needs_ai_review "
            "FROM messages "
            "WHERE category = ? AND length(text) > 20 "
            "ORDER BY RANDOM() LIMIT ?",
            (cat, n),
        ).fetchall()
        for name, text, conf, review in rows:
            flag = " [AI?]" if review else ""
            print(f"  [{name}] (conf={conf}){flag} {text}")
            print()

    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Categorize parsed messages")
    parser.add_argument("--reset", action="store_true", help="Reset all categories")
    parser.add_argument("--stats", action="store_true", help="Show category stats")
    parser.add_argument(
        "--sample", type=int, default=0, help="Show N samples per category",
    )
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
