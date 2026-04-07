from datetime import datetime
import sqlite3
from urllib.parse import quote

from fasthtml.common import *

from components import data_table, ex_card3, layout
from db_schema import DB_PATH


def register(rt):
    @rt("/dashboard")
    def dashboard(request, session):
        headers = ["Client", "Phone", "CNR", "Reg No", "Case Type", "Court", "Next Hearing", "Sub Stage"]
        uid = session["user_id"]
        today = datetime.now().strftime("%d-%m-%Y")

        conn = sqlite3.connect(DB_PATH)
        try:
            my_cases = conn.execute(
                "SELECT client_name, phone, cnr_number, registration_number, case_type, court_name, next_hearing_date, sub_stage FROM cases WHERE user_id=?",
                (uid,),
            ).fetchall()
            appointments_today = conn.execute(
                "SELECT COUNT(*) FROM events WHERE user_id=? AND event_date=?",
                (uid, today),
            ).fetchone()[0]
        finally:
            conn.close()

        total_cases = len(my_cases)
        hearings_today = sum(1 for c in my_cases if (c[6] or "").strip() == today)

        rows = [
            (
                c[0],
                c[1],
                A(
                    c[2],
                    href=f"/client_details?cnr={quote(c[2], safe='')}",
                    cls="text-blue-600 underline hover:text-blue-800 font-medium",
                ),
                c[3],
                c[4],
                c[5],
                c[6],
                c[7],
            )
            for c in my_cases
        ]

        return layout(
            Div(
                ex_card3(total_cases, hearings_today, appointments_today),
                data_table(headers, rows, table_id="maintable"),
            ),
            request,
        )
