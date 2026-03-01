"""Export parsed Telegram data to JSON files for the Astro site.

Reads data/chats/messages.db and generates JSON files into
site/src/data/generated/ for use by Astro pages.

Usage:
    cd parser && python3 export_for_site.py
"""

import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "chats" / "messages.db"
OUTPUT_DIR = Path(__file__).parent.parent / "site" / "src" / "data" / "generated"

# Subcategory -> problem page slug mapping
SUBCAT_TO_SLUG: dict[str, str | None] = {
    "parking": "parking",
    "skud": "skud",
    "water": "communications",
    "elevator": "communications",
    "repair": "repair",
    "territory": "territory",
    "cameras": "video",
    "security": "security",
    "uk": "management-quality",
    "fees": "capital-repair",
    "ventilation": None,
    "cleaning": "territory",
    "intercom": "skud",
    "lighting": "territory",
    "insects": None,
    "noise": None,
    "oss": None,
    "electricity": None,
}

SUBCAT_LABELS: dict[str, str] = {
    "parking": "Паркинг и кладовки",
    "skud": "СКУД и ворота",
    "water": "Водоснабжение и отопление",
    "elevator": "Лифты",
    "repair": "Текущий ремонт",
    "territory": "Территория и благоустройство",
    "cameras": "Видеонаблюдение",
    "security": "Охрана и безопасность",
    "uk": "Управляющая компания",
    "fees": "Тарифы и начисления",
    "ventilation": "Вентиляция и рекуперация",
    "cleaning": "Уборка",
    "intercom": "Домофоны",
    "lighting": "Освещение",
    "insects": "Насекомые и дезинсекция",
    "noise": "Шум",
    "oss": "Общие собрания (ОСС)",
    "electricity": "Электричество",
}


def _clean_text(text: str) -> str:
    """Remove URLs, mentions, and clean up whitespace."""
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_useful_question(text: str) -> bool:
    """Filter out very short or noisy messages."""
    cleaned = _clean_text(text)
    if len(cleaned) < 20:
        return False
    if cleaned.count("?") > 3:
        return False
    # Skip messages that are mostly URLs or emojis
    alpha_chars = sum(1 for c in cleaned if c.isalpha())
    if alpha_chars < 10:
        return False
    return True


def _deduplicate_texts(texts: list[str], max_items: int = 15) -> list[str]:
    """Deduplicate similar texts, keep max_items."""
    seen_normalized: set[str] = set()
    result: list[str] = []
    for text in texts:
        normalized = re.sub(r"\s+", " ", text.lower().strip())
        # Skip if we've seen something very similar (first 50 chars)
        key = normalized[:50]
        if key in seen_normalized:
            continue
        seen_normalized.add(key)
        result.append(text)
        if len(result) >= max_items:
            break
    return result


def export_faq_clusters(db: sqlite3.Connection) -> list[dict]:
    """Generate FAQ clusters grouped by subcategory."""
    rows = db.execute(
        """SELECT subcategory, text FROM messages
           WHERE category = 'faq' AND subcategory IS NOT NULL
           AND text IS NOT NULL AND length(text) > 15
           ORDER BY confidence DESC"""
    ).fetchall()

    clusters: dict[str, list[str]] = defaultdict(list)
    for subcat, text in rows:
        if _is_useful_question(text):
            clusters[subcat].append(_clean_text(text))

    result = []
    for subcat, questions in sorted(clusters.items(), key=lambda x: -len(x[1])):
        deduped = _deduplicate_texts(questions)
        result.append({
            "subcategory": subcat,
            "label": SUBCAT_LABELS.get(subcat, subcat),
            "count": len(questions),
            "problemSlug": SUBCAT_TO_SLUG.get(subcat),
            "questions": deduped,
        })
    return result


def export_problem_stats(db: sqlite3.Connection) -> dict:
    """Generate problem statistics by subcategory with monthly trends."""
    # Count by subcategory
    rows = db.execute(
        """SELECT subcategory, COUNT(*) as cnt FROM messages
           WHERE category = 'problem' AND subcategory IS NOT NULL
           GROUP BY subcategory ORDER BY cnt DESC"""
    ).fetchall()

    stats_by_subcat = {}
    for subcat, cnt in rows:
        stats_by_subcat[subcat] = {
            "subcategory": subcat,
            "label": SUBCAT_LABELS.get(subcat, subcat),
            "count": cnt,
            "problemSlug": SUBCAT_TO_SLUG.get(subcat),
            "quotes": [],
            "monthlyTrend": [],
        }

    # Get anonymous quotes (from problem messages)
    for subcat in stats_by_subcat:
        quote_rows = db.execute(
            """SELECT text FROM messages
               WHERE category = 'problem' AND subcategory = ?
               AND text IS NOT NULL AND length(text) > 30
               AND confidence > 0.4
               ORDER BY confidence DESC LIMIT 30""",
            (subcat,),
        ).fetchall()
        raw_quotes = [_clean_text(r[0]) for r in quote_rows if _is_useful_question(r[0])]
        stats_by_subcat[subcat]["quotes"] = _deduplicate_texts(raw_quotes, max_items=5)

    # Monthly trend for all problems
    trend_rows = db.execute(
        """SELECT substr(date, 1, 7) as month, subcategory, COUNT(*) as cnt
           FROM messages
           WHERE category = 'problem' AND subcategory IS NOT NULL
           GROUP BY month, subcategory
           ORDER BY month"""
    ).fetchall()

    trend_by_subcat: dict[str, list[dict]] = defaultdict(list)
    for month, subcat, cnt in trend_rows:
        trend_by_subcat[subcat].append({"month": month, "count": cnt})

    for subcat, trend in trend_by_subcat.items():
        if subcat in stats_by_subcat:
            stats_by_subcat[subcat]["monthlyTrend"] = trend

    # Also count all discussion mentions (faq + problem + topic)
    discussion_rows = db.execute(
        """SELECT subcategory, COUNT(*) as cnt FROM messages
           WHERE category IN ('faq', 'problem', 'topic', 'solution')
           AND subcategory IS NOT NULL
           GROUP BY subcategory"""
    ).fetchall()

    discussion_counts: dict[str, int] = {}
    for subcat, cnt in discussion_rows:
        discussion_counts[subcat] = cnt

    return {
        "totalProblems": sum(s["count"] for s in stats_by_subcat.values()),
        "bySubcategory": list(stats_by_subcat.values()),
        "discussionCounts": discussion_counts,
    }


def export_solutions(db: sqlite3.Connection) -> list[dict]:
    """Export solution messages grouped by subcategory."""
    rows = db.execute(
        """SELECT subcategory, text, date FROM messages
           WHERE category = 'solution' AND subcategory IS NOT NULL
           AND text IS NOT NULL AND length(text) > 20
           ORDER BY date DESC"""
    ).fetchall()

    by_subcat: dict[str, list[dict]] = defaultdict(list)
    for subcat, text, date in rows:
        cleaned = _clean_text(text)
        if len(cleaned) > 15:
            by_subcat[subcat].append({
                "text": cleaned[:300],
                "date": date[:10] if date else None,
            })

    result = []
    for subcat, items in sorted(by_subcat.items(), key=lambda x: -len(x[1])):
        # Deduplicate
        seen: set[str] = set()
        unique_items = []
        for item in items:
            key = item["text"][:50].lower()
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        result.append({
            "subcategory": subcat,
            "label": SUBCAT_LABELS.get(subcat, subcat),
            "problemSlug": SUBCAT_TO_SLUG.get(subcat),
            "count": len(items),
            "items": unique_items[:10],
        })
    return result


def export_activity_timeline(db: sqlite3.Connection) -> list[dict]:
    """Monthly activity aggregation."""
    rows = db.execute(
        """SELECT
             substr(date, 1, 7) as month,
             COUNT(*) as total,
             SUM(CASE WHEN category = 'problem' THEN 1 ELSE 0 END) as problems,
             SUM(CASE WHEN category = 'faq' THEN 1 ELSE 0 END) as faq,
             SUM(CASE WHEN category = 'solution' THEN 1 ELSE 0 END) as solutions
           FROM messages
           WHERE date IS NOT NULL
           GROUP BY month
           ORDER BY month"""
    ).fetchall()

    return [
        {
            "month": month,
            "total": total,
            "problems": problems,
            "faq": faq,
            "solutions": solutions,
        }
        for month, total, problems, faq, solutions in rows
    ]


def export_contacts_services(db: sqlite3.Connection) -> list[dict]:
    """Extract recommended services/contractors from contact messages.

    Only extracts business/service contacts, NOT personal resident data.
    """
    rows = db.execute(
        """SELECT text, subcategory FROM messages
           WHERE category = 'contact'
           AND text IS NOT NULL AND length(text) > 20
           ORDER BY date DESC"""
    ).fetchall()

    # Extract phone numbers from text
    phone_re = re.compile(r"\+7[\s\-\(]?\d{3}[\s\-\)]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}")

    contacts = []
    seen_phones: set[str] = set()
    for text, subcat in rows:
        phones = phone_re.findall(text)
        for phone in phones:
            normalized = re.sub(r"[\s\-\(\)]", "", phone)
            if normalized in seen_phones:
                continue
            seen_phones.add(normalized)
            contacts.append({
                "phone": phone.strip(),
                "context": _clean_text(text)[:200],
                "subcategory": subcat,
            })

    return contacts


def compute_summary(db: sqlite3.Connection) -> dict:
    """Compute summary stats for the homepage."""
    total = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    faq_count = db.execute(
        "SELECT COUNT(*) FROM messages WHERE category = 'faq'"
    ).fetchone()[0]
    problem_count = db.execute(
        "SELECT COUNT(*) FROM messages WHERE category = 'problem'"
    ).fetchone()[0]
    solution_count = db.execute(
        "SELECT COUNT(*) FROM messages WHERE category = 'solution'"
    ).fetchone()[0]

    # Top discussed subcategories (across faq + problem + topic)
    top_rows = db.execute(
        """SELECT subcategory, COUNT(*) as cnt FROM messages
           WHERE category IN ('faq', 'problem', 'topic')
           AND subcategory IS NOT NULL
           GROUP BY subcategory ORDER BY cnt DESC LIMIT 5"""
    ).fetchall()

    date_range = db.execute(
        "SELECT MIN(date), MAX(date) FROM messages"
    ).fetchone()

    return {
        "totalMessages": total,
        "faqCount": faq_count,
        "problemCount": problem_count,
        "solutionCount": solution_count,
        "topSubcategories": [
            {
                "subcategory": subcat,
                "label": SUBCAT_LABELS.get(subcat, subcat),
                "count": cnt,
                "problemSlug": SUBCAT_TO_SLUG.get(subcat),
            }
            for subcat, cnt in top_rows
        ],
        "dateRange": {
            "from": date_range[0][:10] if date_range[0] else None,
            "to": date_range[1][:10] if date_range[1] else None,
        },
        "exportedAt": datetime.now().isoformat(timespec="seconds"),
    }


def main() -> None:
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        print("Run parser first: cd parser && python3 chat_parser.py")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(DB_PATH))

    exports = {
        "faq-clusters.json": export_faq_clusters,
        "problem-stats.json": export_problem_stats,
        "solutions.json": export_solutions,
        "activity-timeline.json": export_activity_timeline,
        "contacts-services.json": export_contacts_services,
        "summary.json": compute_summary,
    }

    for filename, func in exports.items():
        data = func(db)
        out_path = OUTPUT_DIR / filename
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # Count items
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict) and "bySubcategory" in data:
            count = len(data["bySubcategory"])
        else:
            count = 1
        print(f"  {filename}: {count} items")

    db.close()
    print(f"\nDone. Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
