import json
import sqlite3

from fasthtml.common import *
from monsterui.all import *

from capsolver_ecourts import scrape_ecourts
from components import (
    ClientDetails,
    MonsterForm,
    MonsterForm1,
    data_table,
    error_banner,
    layout,
    simple_calendar,
    success_banner,
)
from db_schema import (
    DB_PATH,
    insertion,
)
from logger import logger
from validation import (
    MAX_HISTORY_JSON_CHARS,
    validate_case_save,
    validate_cnr,
    validate_history_list,
)


def db_case_lookup_fragment(cnr: str, user_id: int):
    conn = sqlite3.connect(DB_PATH)
    try:
        existing = conn.execute(
            "SELECT id, client_name, phone, registration_number, case_type, court_name FROM cases WHERE cnr_number=? AND user_id=?",
            (cnr, int(user_id)),
        ).fetchall()
        if not existing:
            return Div(error_banner("No case found for this CNR."), cls="space-y-4")

        case_ids = [r[0] for r in existing]
        if len(case_ids) == 1:
            hist_rows = conn.execute(
                "SELECT judge, hearing_date, purpose FROM case_history WHERE case_id=? OR (case_id IS NULL AND cnr_number=?)",
                (case_ids[0], cnr),
            ).fetchall()
        else:
            ph = ",".join("?" * len(case_ids))
            hist_rows = conn.execute(
                f"SELECT judge, hearing_date, purpose FROM case_history WHERE case_id IN ({ph}) OR (case_id IS NULL AND cnr_number=?)",
                tuple(case_ids) + (cnr,),
            ).fetchall()
    finally:
        conn.close()

    headers = ["Client", "Phone", "Reg No", "Case Type", "Court"]
    rows = [(r[1], r[2], r[3], r[4], r[5]) for r in existing]
    history_headers = ["Court", "Hearing_date", "Purpose"]
    history_rows = [(r[0], r[1], r[2]) for r in hist_rows]
    return Div(
        data_table(headers, rows, table_id="caseTable"),
        data_table(history_headers, history_rows, table_id="historyTable"),
        cls="space-y-4",
    )


def register(rt):
    @rt("/case")
    def case(request):
        return layout(MonsterForm1(), request)

    @rt("/calendar_new")
    def calendar_new(request):
        return layout(simple_calendar(), request)

    @rt("/client_details")
    def client_details(request, session):
        cnr = (request.query_params.get("cnr") or "").strip()
        results_inner = (
            db_case_lookup_fragment(cnr, session["user_id"])
            if cnr
            else Div(
                P("Enter a CNR and click Fetch.", cls="text-gray-500 p-4"),
                cls="space-y-4",
            )
        )
        return layout(
            Div(
                ClientDetails(cnr_prefill=cnr),
                Div(results_inner, id="case-results"),
                cls="space-y-6",
            ),
            request,
        )

    @rt("/calendar/{year}/{month}")
    def calendar_month(year: int, month: int):
        return simple_calendar(year, month)

    @rt("/dbfetchcase")
    async def post_dbfetchcase(cnr: str, session):
        cnr_clean, cerr = validate_cnr(cnr)
        if cerr:
            return Div(error_banner(cerr, dismiss=False), cls="space-y-4")
        return db_case_lookup_fragment(cnr_clean, session["user_id"])

    @rt("/fetchcase")
    async def post_fetchcase(cnr: str, session):
        uid = session["user_id"]
        cnr_clean, cerr = validate_cnr(cnr)
        if cerr:
            return error_banner(cerr, dismiss=False)
        logger.info("fetchcase start cnr=%s user_id=%s", cnr_clean, uid)
        conn = sqlite3.connect(DB_PATH)
        try:
            existing = conn.execute(
                "SELECT id FROM cases WHERE cnr_number=? AND user_id=? LIMIT 1",
                (cnr_clean, int(uid)),
            ).fetchone()
        finally:
            conn.close()
        if existing:
            logger.warning("fetchcase duplicate cnr=%s user_id=%s", cnr, uid)
            return Div(
                Modal(
                    ModalTitle("Case already exists"),
                    ModalCloseButton("Close", cls=ButtonT.destructive, onclick="window.location='/case'"),
                    id="my-modal",
                ),
                Script("UIkit.modal('#my-modal').show();"),
            )

        case = await scrape_ecourts(cnr_clean)
        if not case:
            logger.error("fetchcase scrape failed cnr=%s user_id=%s", cnr_clean, uid)
            return error_banner("Failed to retrieve case details. Please try again.", dismiss=False)

        case["cnr"] = cnr_clean
        logger.info("fetchcase ok cnr=%s user_id=%s", cnr_clean, uid)
        return MonsterForm(case)

    @rt("/savecase", methods=["POST"])
    def save_case(
        session,
        case_title: str,
        client_name: str,
        phone: str,
        email: str,
        cnr: str,
        regno: str,
        court: str,
        filing: str,
        ctype: str,
        next_hearing_date: str,
        case_stage: str,
        sub_stage: str,
        history_list: str,
    ):
        uid = session["user_id"]
        if len(history_list) > MAX_HISTORY_JSON_CHARS:
            return error_banner("Case history data is too large.", dismiss=False)

        vd, verr = validate_case_save(
            case_title,
            client_name,
            phone,
            email,
            cnr,
            regno,
            court,
            filing,
            ctype,
            next_hearing_date,
            case_stage,
            sub_stage,
        )
        if verr:
            return error_banner(verr, dismiss=False)

        try:
            parsed_history = json.loads(history_list)
        except json.JSONDecodeError:
            logger.exception("savecase invalid history_list JSON user_id=%s cnr=%s", uid, vd["cnr"])
            return error_banner("Could not save: invalid case history data.", dismiss=False)

        rows, herr = validate_history_list(parsed_history)
        if herr:
            return error_banner(herr, dismiss=False)

        try:
            insertion(
                uid,
                vd["cnr"],
                vd["case_title"],
                vd["client_name"],
                vd["phone"],
                vd["email"],
                vd["regno"],
                vd["ctype"],
                vd["court"],
                vd["filing"],
                vd["next_hearing_date"],
                vd["case_stage"],
                vd["sub_stage"],
                rows,
            )
        except Exception:
            logger.exception("savecase insertion failed user_id=%s cnr=%s", uid, vd["cnr"])
            return error_banner("Could not save to database. Please try again.", dismiss=False)

        return Div(
            success_banner("Case saved successfully!"),
            Script("setTimeout(function(){ window.location='/case'; }, 1800);"),
        )