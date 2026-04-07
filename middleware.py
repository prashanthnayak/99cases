import secrets

from csrf import ensure_csrf_token
from rate_limit import is_rate_limited
from starlette.responses import HTMLResponse, RedirectResponse

login_redir = RedirectResponse("/login", status_code=303)

CSRF_POST_PATHS = frozenset(
    {"/savecase", "/save_appointment", "/dbfetchcase", "/fetchcase", "/logout"}
)
LOGIN_RL_MAX, LOGIN_RL_WINDOW = 20, 900.0
FETCHCASE_RL_MAX, FETCHCASE_RL_WINDOW = 40, 3600.0
DBFETCH_RL_MAX, DBFETCH_RL_WINDOW = 120, 3600.0


def _csrf_ok(req, sess) -> bool:
    token = sess.get("csrf_token")
    if not token:
        return False
    sent = req.headers.get("x-csrf-token") or req.headers.get("X-CSRF-Token")
    if not sent:
        return False
    try:
        return secrets.compare_digest(str(token), str(sent))
    except Exception:
        return False


def _client_ip(req) -> str:
    c = req.client
    return c.host if c else "unknown"


def csrf_fail_response():
    return HTMLResponse(
        '<div class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700 text-sm font-medium">'
        "Security check failed. Please refresh the page and try again.</div>",
        status_code=403,
    )


def rate_limit_response(msg="Too many requests. Please try again later."):
    return HTMLResponse(
        '<div class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700 text-sm font-medium">'
        f"{msg}</div>",
        status_code=429,
    )


def before(req, sess):
    req.scope["auth"] = sess.get("user_id", None)
    path = req.url.path
    ensure_csrf_token(sess)

    if path == "/favicon.ico":
        return None

    if path == "/login":
        if req.method == "POST":
            ip = _client_ip(req)
            if is_rate_limited(f"login:{ip}", LOGIN_RL_MAX, LOGIN_RL_WINDOW):
                return rate_limit_response("Too many login attempts. Please wait and try again.")
            if not _csrf_ok(req, sess):
                return csrf_fail_response()
        return None

    auth = sess.get("user_id")
    if not auth:
        return login_redir

    if req.method == "POST":
        if path in CSRF_POST_PATHS and not _csrf_ok(req, sess):
            return csrf_fail_response()
        if path == "/fetchcase":
            if is_rate_limited(f"fetchcase:{auth}", FETCHCASE_RL_MAX, FETCHCASE_RL_WINDOW):
                return rate_limit_response("Too many case fetches. Please try again later.")
        if path == "/dbfetchcase":
            if is_rate_limited(f"dbfetch:{auth}", DBFETCH_RL_MAX, DBFETCH_RL_WINDOW):
                return rate_limit_response("Too many lookups. Please try again later.")

    return None
