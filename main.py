import os
from pathlib import Path

from dotenv import load_dotenv
from fasthtml.common import *
from monsterui.all import *
from starlette.responses import HTMLResponse

from middleware import before
from routes import register_routes

load_dotenv()

hdrs = (
    *Theme.slate.headers(mode="light"),
    Link(rel="stylesheet", href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css"),
    Script(src="https://code.jquery.com/jquery-3.7.0.min.js"),
    Script(src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"),
    Style(
        """
    .display th, .display td { border: 1px solid #ddd !important; padding: 8px !important; }
    .display thead th { background-color: #2563eb !important; color: white !important; }
    .dataTables_wrapper input, .dataTables_wrapper select { background: white !important; color: black !important; }
    .dataTables_wrapper label, .dataTables_wrapper .dataTables_info, .dataTables_wrapper .dataTables_paginate a { color: black !important; }
    .dataTables_wrapper .dataTables_paginate .paginate_button { border: 1px solid #ddd !important; padding: 4px 10px !important; background: white !important; }
    .dataTables_wrapper input { border: 1px solid #ccc !important; border-radius: 4px !important; }
    .dataTables_wrapper input:focus { outline: none !important; box-shadow: none !important; }
"""
    ),
    Script(
        """
/* document exists in <head>; document.body is often null here, so never use body for this. */
document.addEventListener('htmx:configRequest', function (ev) {
  var m = document.querySelector('meta[name="csrf-token"]');
  if (m && m.content) {
    ev.detail.headers['X-CSRF-Token'] = m.content;
  }
});
"""
    ),
)

bware = Beforeware(before, skip=["/favicon.ico"])

_APP_DIR = Path(__file__).resolve().parent


async def not_found(request, exc):
    return HTMLResponse(
        """<!DOCTYPE html><html><body style="font-family:system-ui,sans-serif;text-align:center;margin-top:5rem;">
<h1 style="font-size:1.875rem;font-weight:700;">404 - Page Not Found</h1>
<p style="color:#4b5563;margin-top:0.5rem;">The page you're looking for doesn't exist.</p>
<a href="/dashboard" style="color:#2563eb;margin-top:1rem;display:inline-block;">Go to Dashboard</a>
</body></html>""",
        status_code=404,
    )


async def server_error(request, exc):
    return HTMLResponse(
        """<!DOCTYPE html><html><body style="font-family:system-ui,sans-serif;text-align:center;margin-top:5rem;">
<h1 style="font-size:1.875rem;font-weight:700;color:#dc2626;">500 - Something Went Wrong</h1>
<p style="color:#4b5563;margin-top:0.5rem;">An unexpected error occurred. Please try again.</p>
<a href="/dashboard" style="color:#2563eb;margin-top:1rem;display:inline-block;">Go to Dashboard</a>
</body></html>""",
        status_code=500,
    )


# Session signing: fast_app has no "sess_secret" kwarg (it was ignored). Use SESSION_SECRET
# from the environment, otherwise a stable .sesskey next to this app — not cwd (cwd changes
# break cookies and look like "all data vanished" after restart).
# FastHTML 0.13+: register handlers via exception_handlers= (not @app.exception_handler).
app, rt = fast_app(
    hdrs=hdrs,
    before=bware,
    secret_key=os.getenv("SESSION_SECRET"),
    key_fname=str(_APP_DIR / ".sesskey"),
    exception_handlers={404: not_found, 500: server_error},
)

register_routes(rt)


if __name__ == "__main__":
    serve(port=8003, host="0.0.0.0")
