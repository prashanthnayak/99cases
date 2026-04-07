from fasthtml.common import *
from starlette.responses import RedirectResponse, Response


def register(rt):
    @rt("/favicon.ico")
    def favicon():
        return Response(status_code=204)

    @rt("/hx_empty")
    def hx_empty():
        return Div(cls="hidden", aria_hidden="true")

    @rt("/")
    def index():
        return RedirectResponse("/login")
