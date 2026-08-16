"""Live EUR -> EGP exchange rate with in-memory caching.

Uses the free ECB-backed Frankfurter API, falling back to open.er-api.com.
The /api/rate endpoint exposes this to the frontend for cost conversion.
"""

import time
import threading

import requests

from .config import REQUEST_TIMEOUT

_CACHE = {"rate": None, "updated": 0.0}
_LOCK = threading.Lock()
_CACHE_TTL = 30 * 60  # seconds

_FRANKFURTER = "https://api.frankfurter.app/latest?from=EUR&to=EGP"
_ERAPI = "https://open.er-api.com/v6/latest/EUR"


def _fetch_rate() -> float | None:
    for url in (_FRANKFURTER, _ERAPI):
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            egp = (data.get("rates") or {}).get("EGP")
            if egp:
                return float(egp)
        except Exception:
            continue
    return None


def get_egp_rate(force: bool = False) -> float | None:
    """Return EUR->EGP rate, cached for 30 minutes."""
    now = time.time()
    with _LOCK:
        if not force and _CACHE["rate"] and (now - _CACHE["updated"] < _CACHE_TTL):
            return _CACHE["rate"]

    rate = _fetch_rate()
    if rate:
        with _LOCK:
            _CACHE["rate"] = rate
            _CACHE["updated"] = time.time()
        return rate

    # stale cache as last resort
    with _LOCK:
        return _CACHE["rate"]


if __name__ == "__main__":
    print("EGP rate:", get_egp_rate(force=True))
