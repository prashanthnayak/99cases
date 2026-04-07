import asyncio
import sqlite3
from datetime import datetime

from capsolver_ecourts import scrape_ecourts
from date_normalize import normalize_date_for_db
from db_schema import DB_PATH
from logger import logger


async def update_todays_cases():
    today = datetime.now().strftime("%d-%m-%Y")

    conn = sqlite3.connect(DB_PATH)
    try:
        todays_cases = conn.execute(
            "SELECT id, cnr_number FROM cases WHERE next_hearing_date=?",
            (today,),
        ).fetchall()
    finally:
        conn.close()

    if not todays_cases:
        logger.info("cron: no hearings scheduled for %s", today)
        return

    logger.info("cron: updating %s case(s) for %s", len(todays_cases), today)

    for case_id, cnr in todays_cases:
        logger.info("cron: updating cnr=%s case_id=%s", cnr, case_id)

        scraped = await scrape_ecourts(cnr)
        if not scraped:
            logger.error("cron: scrape failed cnr=%s", cnr)
            continue

        try:
            next_hearing = normalize_date_for_db(scraped.get("next_hearing_date")) or ""
            case_stage = scraped.get("case_stage", "")
            sub_stage = scraped.get("sub_stage", "")

            conn = sqlite3.connect(DB_PATH)
            try:
                conn.execute(
                    "UPDATE cases SET next_hearing_date=?, case_stage=?, sub_stage=? WHERE id=?",
                    (next_hearing, case_stage, sub_stage, case_id),
                )

                existing = {
                    normalize_date_for_db(r[0])
                    for r in conn.execute(
                        "SELECT hearing_date FROM case_history WHERE cnr_number=?",
                        (cnr,),
                    ).fetchall()
                    if r[0]
                }

                for h in scraped.get("case_history", []):
                    hearing_norm = normalize_date_for_db(h.get("hearing_date"))
                    if not hearing_norm or hearing_norm in existing:
                        continue
                    business_norm = normalize_date_for_db(h.get("business_date"))
                    conn.execute(
                        """
                        INSERT INTO case_history (case_id, cnr_number, judge, business_date, hearing_date, purpose)
                        VALUES (?,?,?,?,?,?)
                        """,
                        (case_id, cnr, h["judge"], business_norm, hearing_norm, h.get("purpose")),
                    )
                    existing.add(hearing_norm)

                conn.commit()
            finally:
                conn.close()

        except Exception:
            logger.exception("cron: DB update failed cnr=%s", cnr)
            continue

        logger.info("cron: updated cnr=%s", cnr)


if __name__ == "__main__":
    asyncio.run(update_todays_cases())
