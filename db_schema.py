import os
import sqlite3
from datetime import datetime
from pathlib import Path

from passlib.context import CryptContext

from date_normalize import normalize_date_for_db
from logger import logger


def _resolve_db_path() -> str:
    """One stable DB file. Override with LEGAL_SQLITE_PATH=/abs/or/~/path.sqlite if needed."""
    raw = (os.environ.get("LEGAL_SQLITE_PATH") or "").strip()
    if raw:
        p = Path(raw).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        return str(p)
    return str(Path(__file__).resolve().parent / "legal.sqlite")


DB_PATH = _resolve_db_path()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger.info("Database file (persistent across restarts): %s", DB_PATH)


def _init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS login (
                id            INTEGER PRIMARY KEY,
                name          TEXT,
                email         TEXT,
                password_hash TEXT
            );

            CREATE TABLE IF NOT EXISTS cases (
                id                  INTEGER PRIMARY KEY,
                user_id             INTEGER REFERENCES login(id),
                cnr_number          TEXT,
                case_title          TEXT,
                client_name         TEXT,
                phone               TEXT,
                email               TEXT,
                registration_number TEXT,
                case_type           TEXT,
                court_name          TEXT,
                filing_date         TEXT,
                next_hearing_date   TEXT,
                case_stage          TEXT,
                sub_stage           TEXT,
                created_at          TEXT,
                updated_at          TEXT
            );

            CREATE TABLE IF NOT EXISTS case_history (
                id            INTEGER PRIMARY KEY,
                case_id       INTEGER REFERENCES cases(id),
                cnr_number    TEXT,
                judge         TEXT,
                business_date TEXT,
                hearing_date  TEXT,
                purpose       TEXT
            );

            CREATE TABLE IF NOT EXISTS events (
                id          INTEGER PRIMARY KEY,
                user_id     INTEGER NOT NULL REFERENCES login(id),
                case_id     INTEGER REFERENCES cases(id),
                event_title TEXT,
                event_date  TEXT,
                event_type  TEXT,
                notes       TEXT,
                created_at  TEXT
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


_init_db()


def insertion(
    user_id,
    cnr_number,
    case_title,
    client_name,
    phone,
    email,
    registration_number,
    case_type,
    court_name,
    filing_date,
    next_hearing_date,
    case_stage,
    sub_stage,
    history_list,
):
    try:
        filing_norm = normalize_date_for_db(filing_date)
        next_hearing_norm = normalize_date_for_db(next_hearing_date)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.execute(
                """
                INSERT INTO cases
                  (user_id, cnr_number, case_title, client_name, phone, email,
                   registration_number, case_type, court_name, filing_date,
                   next_hearing_date, case_stage, sub_stage, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    int(user_id), cnr_number, case_title, client_name, phone, email,
                    registration_number, case_type, court_name, filing_norm,
                    next_hearing_norm, case_stage, sub_stage, now, now,
                ),
            )
            case_id = int(cur.lastrowid)

            for history in history_list:
                business_norm = normalize_date_for_db(history.get("business_date"))
                hearing_norm = normalize_date_for_db(history.get("hearing_date"))
                conn.execute(
                    """
                    INSERT INTO case_history
                      (case_id, cnr_number, judge, business_date, hearing_date, purpose)
                    VALUES (?,?,?,?,?,?)
                    """,
                    (
                        case_id, cnr_number, history["judge"],
                        business_norm, hearing_norm, history.get("purpose"),
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO events
                      (user_id, case_id, event_title, event_date, event_type, created_at)
                    VALUES (?,?,?,?,?,?)
                    """,
                    (
                        int(user_id), case_id,
                        f"Hearing - {history.get('purpose', 'Court Hearing')}",
                        hearing_norm, "court_hearing", now,
                    ),
                )

            conn.commit()
        finally:
            conn.close()

        logger.info(
            "insertion ok user_id=%s cnr=%s case_id=%s history_rows=%s",
            user_id, cnr_number, case_id, len(history_list),
        )
        return case_id
    except Exception:
        logger.exception("insertion failed user_id=%s cnr=%s", user_id, cnr_number)
        raise


def create_user(name, email, password):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            "INSERT INTO login (name, email, password_hash) VALUES (?,?,?)",
            (name, email, pwd_context.hash(password)),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def add_appointment(user_id, event_title, event_date, event_type, notes):
    """Insert a non-court appointment (case_id=NULL). Uses explicit commit for durability."""
    date_norm = normalize_date_for_db(event_date)
    created = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            """
            INSERT INTO events (user_id, case_id, event_title, event_date, event_type, notes, created_at)
            VALUES (?, NULL, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                (event_title or "").strip(),
                date_norm,
                (event_type or "").strip(),
                (notes or "").strip(),
                created,
            ),
        )
        conn.commit()
        eid = int(cur.lastrowid)
    finally:
        conn.close()
    logger.info("add_appointment ok user_id=%s event_id=%s (non-court)", user_id, eid)
    return eid


def get_user_by_name(name: str):
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            "SELECT id, name, password_hash FROM login WHERE name=?", (name,)
        ).fetchone()
        if row:
            return {"id": row[0], "name": row[1], "password_hash": row[2]}
        return None
    finally:
        conn.close()
