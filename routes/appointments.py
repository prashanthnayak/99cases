from datetime import datetime
import sqlite3

from fasthtml.common import *

from components import (
    appointment_form_card,
    data_table,
    error_banner,
    layout,
    success_banner,
)
from db_schema import DB_PATH, add_appointment
from logger import logger
from validation import validate_appointment


def appointments_table_rows(user_id):
    conn = sqlite3.connect(DB_PATH)
    try:
        raw_rows = conn.execute(
            """
            SELECT event_date, event_title, event_type, notes
            FROM events
            WHERE user_id=? AND case_id IS NULL
            """,
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    events_list = [
        {
            "event_date": r[0] or "",
            "event_title": r[1] or "",
            "event_type": r[2] or "",
            "notes": r[3] or "",
        }
        for r in raw_rows
    ]

    def sort_key(e):
        d = e.get("event_date") or ""
        try:
            return datetime.strptime(d, "%d-%m-%Y")
        except (ValueError, TypeError):
            return datetime.min

    events_list.sort(key=sort_key, reverse=True)
    headers = ["Date", "Title", "Place", "Notes"]
    rows = [
        (
            e.get("event_date") or "",
            e.get("event_title") or "",
            e.get("event_type") or "",
            e.get("notes") or "",
        )
        for e in events_list
    ]
    return headers, rows


def appointments_panel(user_id, success_message=None, error_message=None):
    headers, rows = appointments_table_rows(user_id)
    top = []
    if error_message:
        top.append(error_banner(error_message))
    if success_message:
        top.append(success_banner(success_message))
    slot_inner = [appointment_form_card()] if error_message else []
    return Div(
        *top,
        Div(*slot_inner, id="appointment-form-slot", cls="mb-8"),
        data_table(headers, rows, table_id="appointmentsTable"),
        id="appointments-panel",
        cls="space-y-2 mt-4",
    )


def register(rt):
    @rt("/appointments")
    def appointments(request, session):
        uid = session["user_id"]
        return layout(
            Div(
                Div(
                    H2("Appointments", cls="text-2xl font-bold text-gray-800 tracking-tight"),
                    P(
                        "Non-court appointments only (not linked to a case). Court hearings stay on case import.",
                        cls="text-gray-600 text-sm mt-1 max-w-2xl",
                    ),
                    Button(
                        "Add a new appointment",
                        cls="mt-5 inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium shadow-md transition-colors",
                        hx_get="/appointment_form_fragment",
                        hx_target="#appointment-form-slot",
                        hx_swap="innerHTML",
                    ),
                    cls="mb-2",
                ),
                appointments_panel(uid),
                cls="space-y-2",
            ),
            request,
        )

    @rt("/appointment_form_fragment")
    def appointment_form_fragment(request, session):
        return appointment_form_card()

    @rt("/appointment_form_clear")
    def appointment_form_clear(request, session):
        return Div()

    @rt("/save_appointment", methods=["POST"])
    def save_appointment(
        session,
        event_title: str,
        event_date: str,
        event_type: str = "",
        notes: str = "",
    ):
        uid = session["user_id"]
        vd, verr = validate_appointment(event_title, event_date, event_type, notes)
        if verr:
            return appointments_panel(uid, error_message=verr)
        try:
            add_appointment(uid, vd["event_title"], vd["event_date"], vd["event_type"], vd["notes"])
        except Exception:
            logger.exception("save_appointment failed user_id=%s", uid)
            return appointments_panel(uid, error_message="Could not save appointment. Please try again.")
        return appointments_panel(uid, success_message="Appointment saved.")
