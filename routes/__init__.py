from routes import appointments, auth, cases, dashboard, misc


def register_routes(rt):
    misc.register(rt)
    auth.register(rt)
    dashboard.register(rt)
    cases.register(rt)
    appointments.register(rt)
