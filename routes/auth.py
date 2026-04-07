import secrets

from fasthtml.common import Redirect
from starlette.responses import RedirectResponse

from components import error_banner, login_page
from csrf import ensure_csrf_token
from db_schema import get_user_by_name, pwd_context
from logger import logger
from validation import validate_login


def register(rt):
    @rt("/login", methods=["GET", "HEAD"])
    def get_login(session):
        ensure_csrf_token(session)
        return login_page(session["csrf_token"])

    @rt("/login", methods=["POST"])
    def post_login(username: str, password: str, session):
        creds, verr = validate_login(username, password)
        if verr:
            return error_banner(verr, dismiss=False)
        user = get_user_by_name(creds[0])

        if user and pwd_context.verify(creds[1], user["password_hash"]):
            session["user_id"] = user["id"]
            session["username"] = user["name"]
            session["csrf_token"] = secrets.token_urlsafe(32)
            logger.info("login ok user_id=%s username=%s", user["id"], creds[0])
            return Redirect("/dashboard")

        logger.warning("login failed username=%s", creds[0])
        return error_banner("Invalid username or password", dismiss=False)

    @rt("/logout", methods=["GET"])
    def logout_get(session):
        session.clear()
        return RedirectResponse("/login", status_code=303)

    @rt("/logout", methods=["POST"])
    def logout_post(session):
        session.clear()
        return Redirect("/login")
