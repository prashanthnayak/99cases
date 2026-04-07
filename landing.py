"""Run the app with `python main.py` or `uvicorn main:app`. This file re-exports `app` for `uvicorn landing:app`."""

from main import app

if __name__ == "__main__":
    from fasthtml.common import serve

    serve(
        port=8003,
        host="0.0.0.0",
        # If you ever widen reload patterns, SQLite / logs must not trigger restarts.
        reload_excludes=["*.sqlite", "*.sqlite-wal", "*.sqlite-shm", "app.log", ".sesskey"],
    )
