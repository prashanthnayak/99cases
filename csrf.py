import secrets


def ensure_csrf_token(sess):
    if not sess.get("csrf_token"):
        sess["csrf_token"] = secrets.token_urlsafe(32)
