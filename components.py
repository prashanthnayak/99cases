import calendar
import json
from datetime import datetime
from urllib.parse import quote

from fasthtml.common import *
from monsterui.all import *


def MonsterForm1():
    return Div(
        LabelInput(
            "CNR Number",
            id="cnr-inp",
            name="cnr",
            input_cls="rounded-lg border-gray-300 max-w-sm",
            lbl_cls="mr-4",
            required=True,
        ),
        Div(
            Button(
                "Fetch",
                hx_post="/fetchcase",
                hx_include="[name='cnr']",
                hx_target="#monsterform1",
                hx_indicator="#spinner",
                cls="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg mt-4",
            ),
            Div(
                Loading(cls=(LoadingT.spinner, LoadingT.lg), htmx_indicator=True),
                cls="ml-4 mt-2",
                id="spinner",
            ),
            cls="flex items-center gap-2",
        ),
        id="monsterform1",
    )


def MonsterForm(case):
    fcnr = case.get("cnr", "")
    fregno = case.get("registration_number", "")
    fcourt = case.get("court_name", "")
    fcasetype = case.get("case_type", "")
    fsubstage = case.get("sub_stage", "")
    ffilingdate = case.get("registration_date", "")
    fnexthearingdate = case.get("next_hearing_date", "")
    fcasestage = case.get("case_stage", "")
    fhistorylist = case.get("case_history", [])
    return Div(
        H2("Add a New Case", cls="text-2xl font-bold mb-6 text-gray-800"),
        Div(id="savecase-errors", cls="min-h-0"),
        Form(
            Input(type="hidden", name="next_hearing_date", value=fnexthearingdate),
            Input(type="hidden", name="case_stage", value=fcasestage),
            Input(type="hidden", name="sub_stage", value=fsubstage),
            Input(type="hidden", name="history_list", value=json.dumps(fhistorylist, indent=4)),
            Grid(
                LabelInput("CNR Number", id="cnr", name="cnr", value=fcnr, required=True, input_cls="rounded-lg border-gray-300"),
                LabelInput("Case Title", id="case_title", name="case_title", required=True, input_cls="rounded-lg border-gray-300"),
                LabelInput("Client Name", id="client_name", name="client_name", required=True, input_cls="rounded-lg border-gray-300"),
                cols=3,
            ),
            Grid(
                LabelInput(
                    "Phone",
                    id="phone",
                    name="phone",
                    required=True,
                    input_cls="rounded-lg border-gray-300",
                ),
                LabelInput(
                    "Email",
                    id="email",
                    name="email",
                    required=True,
                    input_cls="rounded-lg border-gray-300",
                ),
                LabelInput("Reg No.", id="regno", name="regno", value=fregno, input_cls="rounded-lg border-gray-300"),
                cols=3,
            ),
            Grid(
                LabelInput("Case Type", id="ctype", name="ctype", value=fcasetype, input_cls="rounded-lg border-gray-300"),
                LabelInput("Court", id="court", name="court", value=fcourt, input_cls="rounded-lg border-gray-300"),
                LabelInput("Filing Date", id="filing", name="filing", value=ffilingdate, input_cls="rounded-lg border-gray-300"),
                cols=3,
            ),
            DivCentered(Button("Save Case", type="submit", cls="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 mt-4 rounded-lg")),
            hx_post="/savecase",
            hx_target="#savecase-errors",
            hx_swap="innerHTML",
            hx_disabled_elt='button[type="submit"]',
        ),
        cls="space-y-6 p-6 bg-white rounded-lg shadow",
        id="result",
    )


def ClientDetails(cnr_prefill: str = ""):
    return Div(
        LabelInput(
            "CNR Number",
            id="cnr-inp",
            name="cnr",
            value=cnr_prefill,
            input_cls="rounded-lg border-gray-300 max-w-sm",
            lbl_cls="mr-4",
            required=True,
        ),
        Div(
            Button(
                "Fetch",
                hx_post="/dbfetchcase",
                hx_include="[name='cnr']",
                hx_target="#case-results",
                cls="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg mt-4",
            ),
            cls="flex items-center gap-2",
        ),
        id="client-search",
        cls="space-y-2",
    )


def simple_calendar(year=None, month=None):
    if year is None or month is None:
        today = datetime.now()
        year = today.year
        month = today.month
    cal = calendar.monthcalendar(year, month)

    return Div(
        Div(
            Button(
                "←",
                hx_get=f"/calendar/{year}/{month-1}",
                hx_target="#cal_func",
                cls="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700",
            ),
            H2(f"{calendar.month_name[month]} {year}", cls="text-2xl font-bold text-gray-800"),
            Button(
                "→",
                hx_get=f"/calendar/{year}/{month+1}",
                hx_target="#cal_func",
                cls="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700",
            ),
            cls="flex justify-between items-center mb-4",
        ),
        Grid(
            *[Div(day, cls="text-center font-bold bg-gray-100 p-2 text-gray-700") for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]],
            cols=7,
        ),
        Grid(
            *[Div(str(day) if day != 0 else "", cls="border border-gray-200 p-3 text-center hover:bg-blue-50 text-gray-700") for week in cal for day in week],
            cols=7,
        ),
        cls="border border-gray-200 p-6 bg-white rounded-lg shadow",
        id="cal_func",
    )


def page_headers(request):
    username = request.session.get("username", "User")
    return Div(
        Div(
            H2(
                f"Diary of Advocate {username}",
                cls="text-2xl font-bold text-blue-900 text-center truncate w-full capitalize",
            ),
            Button(
                "Logout",
                cls="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700",
                hx_post="/logout",
                hx_swap="none",
            ),
            cls="flex justify-between  items-center",
        ),
        cls="bg-white p-6 mb-6 rounded-lg shadow",
    )


def company_title():
    return Div(
        Div(
            Img(src="shri.png", cls="w-20 h-20 mr-3"),
            Div(
                H1("99Cases", cls="text-left text-3xl font-bold text-blue-600 tracking-wide"),
                P("Legal Management System", cls="mt-1 text-left text-xs text-gray-500"),
            ),
            cls="flex items-center",
        ),
        cls="mb-8 border-b border-gray-200 pb-4 pt-6 text-left",
    )


def login_page(csrf_token: str):
    return Div(
        Meta(name="csrf-token", content=csrf_token),
        Style(
            """
    body { margin: 0; }
    .aurora-bg {
        position: fixed; inset: 0;
        background: linear-gradient(135deg, #0f172a, #1e1b4b, #0f172a);
        overflow: hidden;
        z-index: 0;
    }
    .aurora-bg::before, .aurora-bg::after {
        content: '';
        position: absolute;
        border-radius: 50%;
        filter: blur(80px);
        opacity: 0.5;
        animation: aurora 10s ease-in-out infinite alternate;
    }
    .aurora-bg::before {
        width: 600px; height: 600px;
        background: #6366f1;
        top: -100px; left: -100px;
    }
    .aurora-bg::after {
        width: 500px; height: 500px;
        background: #06b6d4;
        bottom: -100px; right: -100px;
        animation-delay: -5s;
    }
    @keyframes aurora {
        0% { transform: scale(1) translate(0, 0); }
        100% { transform: scale(1.3) translate(50px, 50px); }
    }
"""
        ),
        Div(cls="aurora-bg"),
        DivCentered(cls="min-h-screen relative z-10")(
            H1("99Cases", cls="text-5xl font-bold text-white text-center mb-2"),
            P("Legal Case Management", cls="text-indigo-300 text-center mb-8 text-lg"),
            Form(
                Div(cls="text-red-600 text-center mb-4", id="error-msg"),
                LabelInput("Username", name="username", id="username", input_cls="w-full"),
                LabelInput("Password", name="password", id="password", type="password", input_cls="w-full"),
                Div(cls="h-4"),
                Button("Login", cls="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg w-full"),
                cls="bg-white p-16 shadow-lg w-96 space-y-4 rounded-xl",
                hx_post="/login",
                hx_target="#error-msg",
                hx_headers=json.dumps({"X-CSRF-Token": csrf_token}),
            ),
        ),
        cls="relative overflow-hidden min-h-screen",
    )


def ex_card3(total_cases: int, hearings_today: int, appointments_today: int):
    def dash_card(name, value=""):
        return Card(
            Div(
                H3(name, cls="text-lg font-semibold text-gray-700 mb-2"),
                P(value, cls="text-3xl font-bold text-blue-600") if value else Div(cls="h-32 bg-gray-100 rounded"),
                cls="p-6",
            ),
            cls="bg-white rounded-lg shadow hover:shadow-lg transition-all",
        )

    team = [
        dash_card("Total Cases", str(total_cases)),
        dash_card("Hearings Today", str(hearings_today)),
        dash_card("Appointments Today", str(appointments_today)),
    ]
    return Grid(*team, cols=3, cls="gap-6")


def data_table(headers, rows, table_id="myTable"):
    # Destroy any previous DataTables instance on this id (same id can reappear after HTMX swaps).
    sid = json.dumps(table_id)
    init_js = f"""
(function() {{
  var $ = window.jQuery;
  if (!$ || !$.fn.DataTable) return;
  var sel = '#' + {sid};
  var $t = $(sel);
  if (!$t.length) return;
  if ($.fn.dataTable.isDataTable(sel)) {{
    $t.DataTable().destroy(true);
  }}
  $t.DataTable();
}})();
"""
    return Div(
        Table(
            Thead(Tr(*[Th(h) for h in headers])),
            Tbody(*[Tr(*[Td(cell) for cell in row]) for row in rows]),
            id=table_id,
            cls="display cell-border",
            style="width: 100%;",
        ),
        Script(init_js),
        cls="p-6 mt-8",
    )


def _flash_dismiss_attrs():
    return dict(
        hx_get="/hx_empty",
        hx_trigger="revealed delay:5s once",
        hx_swap="outerHTML",
    )


def error_banner(msg: str, *, dismiss: bool = True):
    cls = "rounded-lg border border-red-200 bg-red-50 px-4 py-3 mb-4"
    extra = _flash_dismiss_attrs() if dismiss else {}
    return Div(P(msg, cls="text-red-700 text-sm font-medium"), cls=cls, **extra)


def success_banner(msg: str, *, dismiss: bool = True):
    cls = "rounded-lg border border-green-200 bg-green-50 px-4 py-3 mb-4"
    extra = _flash_dismiss_attrs() if dismiss else {}
    return Div(P(msg, cls="text-green-800 text-sm font-medium"), cls=cls, **extra)


_lbl = "text-sm font-medium text-gray-700"
_inp = "w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"


def AppointmentForm():
    return Form(
        Grid(
            LabelInput(
                "Event title",
                id="ev_title",
                name="event_title",
                required=True,
                lbl_cls=_lbl,
                input_cls=_inp,
            ),
            LabelInput(
                "Event date",
                id="ev_date",
                name="event_date",
                placeholder="DD-MM-YYYY",
                required=True,
                lbl_cls=_lbl,
                input_cls=_inp,
            ),
            LabelInput(
                "Place",
                id="ev_place",
                name="event_type",
                placeholder="e.g. office, court building",
                required=True,
                lbl_cls=_lbl,
                input_cls=_inp,
            ),
            cols=3,
            cls="gap-4",
        ),
        Div(
            LabelInput(
                "Notes (optional)",
                id="ev_notes",
                name="notes",
                lbl_cls=_lbl,
                input_cls=_inp,
            ),
            cls="mt-4",
        ),
        Div(
            Button(
                "Cancel",
                type="button",
                cls="px-5 py-2.5 rounded-lg border border-gray-300 bg-white text-gray-700 font-medium hover:bg-gray-50",
                hx_get="/appointment_form_clear",
                hx_target="#appointment-form-slot",
                hx_swap="innerHTML",
            ),
            Button(
                "Save appointment",
                type="submit",
                cls="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-sm",
            ),
            cls="flex flex-wrap justify-end gap-3 mt-8 pt-6 border-t border-gray-100",
        ),
        cls="space-y-1",
        hx_post="/save_appointment",
        hx_target="#appointments-panel",
        hx_swap="outerHTML",
    )


def appointment_form_card():
    return Card(
        Div(
            H3("New appointment", cls="text-xl font-bold text-gray-800"),
            P(
                "Non-court appointments (meetings, deadlines, reminders).",
                cls="text-sm text-gray-500 mt-1 mb-6",
            ),
            AppointmentForm(),
            cls="space-y-2",
        ),
        cls="p-8 bg-white rounded-xl shadow-lg border border-gray-100 max-w-5xl",
        id="appointment-form",
    )


def Nav(request):
    current_path = request.url.path

    def nav_link(text, href):
        is_active = current_path == href
        return A(
            B(text, cls="block min-w-0 w-full text-left text-base"),
            href=href,
            cls=(
                "box-border flex w-full min-w-0 items-center justify-start px-4 py-3 "
                f"{'bg-blue-600 text-white' if is_active else 'hover:bg-gray-300 text-gray-700 bg-white'} "
                "text-left transition-all duration-200"
            ),
        )

    return Div(
        nav_link("Dashboard", "/dashboard"),
        nav_link("Add Case", "/case"),
        nav_link("Clients", "/client_details"),
        nav_link("Appointments", "/appointments"),
        cls="min-w-0 space-y-1 px-2 py-2 text-left sm:px-3 sm:py-3",
    )


def layout(content, request):
    token = request.session.get("csrf_token", "")
    return Div(
        Meta(name="csrf-token", content=token),
        Div(company_title(), Nav(request), cls="w-1/6 bg-gray-50 min-h-screen border-r border-gray-200"),
        Div(page_headers(request), content, cls="w-5/6 bg-gray-50 min-h-screen p-6"),
        cls="flex",
    )
