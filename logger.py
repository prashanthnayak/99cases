import logging
import sys
from pathlib import Path

# Log next to the app, not the shell cwd (avoids split-brain when launching from ~).
LOG_FILE = str(Path(__file__).resolve().parent / "app.log")
_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logger = logging.getLogger("legal_app")
logger.setLevel(logging.INFO)
logger.propagate = False  # Don't pass records to the root logger (keeps watchfiles/uvicorn noise out of app.log)

if not logger.handlers:
    _fmt = logging.Formatter(_FORMAT)
    _fh = logging.FileHandler(LOG_FILE)
    _fh.setFormatter(_fmt)
    _sh = logging.StreamHandler(sys.stderr)
    _sh.setFormatter(_fmt)
    logger.addHandler(_fh)
    logger.addHandler(_sh)
