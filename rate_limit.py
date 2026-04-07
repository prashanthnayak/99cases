"""Simple in-process rate limiting (stdlib only). Not suitable for multi-worker scale-out."""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict

_lock = threading.Lock()
_buckets: Dict[str, Deque[float]] = defaultdict(deque)


def is_rate_limited(key: str, max_events: int, window_sec: float) -> bool:
    """
    Return True if this key has hit the limit (and do not record this attempt).
    Return False and record the attempt if under the limit.
    """
    now = time.time()
    with _lock:
        dq = _buckets[key]
        while dq and now - dq[0] > window_sec:
            dq.popleft()
        if len(dq) >= max_events:
            return True
        dq.append(now)
        return False
