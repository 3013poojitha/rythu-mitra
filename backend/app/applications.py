"""Scheme applications made by farmers in the app ("Apply for a scheme" on Home).

New applications are saved to backend/applications.json and added on top of the
dummy applications in data.py, so they survive a restart. The web app and the
Streamlit app share the file. Delete it to go back to the demo applications only.

A new application starts as "Pending verification": in a real system the AEO
would check the land records and bank details next.
"""
import secrets
import threading
from datetime import date
from pathlib import Path

from . import data

APPS_FILE = Path(__file__).resolve().parents[1] / "applications.json"
NEW_STATUS = "Pending verification"
_lock = threading.Lock()
_seen = [None]  # modification time of the file when we last read it


class ApplicationError(Exception):
    pass


def _mtime():
    try:
        return APPS_FILE.stat().st_mtime
    except FileNotFoundError:
        return None


def sync():
    """Add applications saved by either app (since the last read) to the farmers' lists."""
    if _mtime() == _seen[0]:
        return
    _seen[0] = _mtime()
    for fid, apps in data.read_json(APPS_FILE, {}).items():
        f = data.FARMER_INDEX.get(fid)
        if not f:
            continue
        have = {a["app_id"] for a in f["applications"]}
        f["applications"] += [a for a in apps if a["app_id"] not in have]


def open_schemes(farmer_id):
    """Schemes the farmer can apply for now: any scheme without an application that is
    still going or paid. A rejected application can be made again."""
    sync()
    f = data.FARMER_INDEX[farmer_id]
    busy = {a["scheme_id"] for a in f["applications"] if not a["status"].startswith("Rejected")}
    return [s for s in data.SCHEMES if s["id"] not in busy]


def apply(farmer_id, scheme_id):
    """Make a new application. Returns it; raises ApplicationError if not allowed."""
    f = data.FARMER_INDEX.get((farmer_id or "").upper())
    if not f:
        raise ApplicationError("Farmer not found.")
    scheme = next((s for s in data.SCHEMES if s["id"] == scheme_id), None)
    if not scheme:
        raise ApplicationError("Please choose a scheme.")
    if scheme not in open_schemes(f["farmer_id"]):
        raise ApplicationError("You have already applied for this scheme.")
    app = {"app_id": f"APP-{secrets.randbelow(900000) + 100000}", "scheme_id": scheme_id,
           "applied_on": date.today().isoformat(), "status": NEW_STATUS, "amount": 0, "credited_on": None,
           "channel": "Rythu Mitra app"}
    with _lock:
        saved = data.read_json(APPS_FILE, {})
        saved.setdefault(f["farmer_id"], []).append(app)
        data.write_json(APPS_FILE, saved)
        _seen[0] = _mtime()
        f["applications"].append(app)
    return app


sync()
