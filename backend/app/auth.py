"""User accounts, login sessions and password reset.

* Passwords are never stored in plain text - only a salted PBKDF2 hash.
* Users are saved to backend/users.json so sign-ups and password changes
  survive a restart. Delete that file to go back to the demo accounts.
* Login sessions are random tokens. Only a hash of each token is saved, in
  backend/sessions.json, so a restart does not log anyone out.
* Forgot password sends a 6-digit one-time code (OTP). There is no real SMS or
  email in this demo, so the API also returns the code and the screen shows it.
"""
import hashlib
import hmac
import re
import secrets
import threading
import time
from pathlib import Path

from . import data

USERS_FILE = Path(__file__).resolve().parents[1] / "users.json"
SESSIONS_FILE = Path(__file__).resolve().parents[1] / "sessions.json"
SESSION_HOURS = 8
OTP_MINUTES = 10
MAX_FAILED = 5
LOCK_MINUTES = 5

ROLES = {
    "admin": "Department Admin",
    "contributor": "NISG Contributor",
    "reviewer": "Department Reviewer",
    "bv_central": "Bharat Vistaar Central Team",
    "farmer": "Farmer",
}

# Demo accounts created on first run (also listed in README.md)
DEMO_USERS = [
    {"user_id": "admin", "name": "Dept Admin", "role": "admin", "mobile": "9000000001", "password": "Admin@123"},
    {"user_id": "nisg.contributor", "name": "NISG Contributor", "role": "contributor", "mobile": "9000000002", "password": "Contrib@123"},
    {"user_id": "dept.reviewer", "name": "Department Reviewer", "role": "reviewer", "mobile": "9000000003", "password": "Review@123"},
    {"user_id": "bv.central", "name": "BV Central Team", "role": "bv_central", "mobile": "9000000004", "password": "Central@123"},
    {"user_id": "TS1002", "role": "farmer", "farmer_id": "TS1002", "password": "Farmer@123"},
]

_lock = threading.Lock()
_session_lock = threading.Lock()
USERS = {}      # user_id (lower case) -> user record
SESSIONS = {}   # sha256(token) -> {"user_id", "expires"}
OTPS = {}       # user_id (lower case) -> {"code_hash", "expires", "attempts"}


class AuthError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def _hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
    return f"{salt}${digest}"


def _verify(password, stored):
    salt, _ = stored.split("$", 1)
    return hmac.compare_digest(_hash(password, salt), stored)


def check_strength(password):
    if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise AuthError("Password must be at least 8 characters and contain letters and numbers.")


def _save():
    data.write_json(USERS_FILE, list(USERS.values()))


def _th(token):
    return hashlib.sha256((token or "").encode()).hexdigest()


def _sync_sessions(add=None, remove=()):
    """Merge this process's change into sessions.json. The web app and the
    Streamlit app both use the file, so always start from what is on disk."""
    with _session_lock:
        now = time.time()
        saved = {k: v for k, v in data.read_json(SESSIONS_FILE, {}).items() if v["expires"] > now}
        saved.update(add or {})
        for k in remove:
            saved.pop(k, None)
        data.write_json(SESSIONS_FILE, saved)
        SESSIONS.clear()
        SESSIONS.update(saved)


def _load():
    _sync_sessions()
    if USERS_FILE.exists():
        for u in data.read_json(USERS_FILE, []):
            USERS[u["user_id"].lower()] = u
        return
    for d in DEMO_USERS:
        _create(dict(d), save=False)
    _save()


def _create(d, save=True):
    if d.get("farmer_id"):
        f = data.FARMER_INDEX[d["farmer_id"]]
        d.setdefault("name", f["name"])
        d.setdefault("mobile", f["mobile"])
    user = {"user_id": d["user_id"], "name": d["name"], "role": d["role"], "mobile": d["mobile"],
            "farmer_id": d.get("farmer_id"), "password_hash": _hash(d["password"]),
            "failed": 0, "locked_until": 0, "created": data.now_iso()}
    USERS[user["user_id"].lower()] = user
    if save:
        _save()
    return user


def public(u):
    return {"user_id": u["user_id"], "name": u["name"], "role": u["role"], "role_label": ROLES[u["role"]],
            "farmer_id": u["farmer_id"], "mobile_masked": mask(u["mobile"])}


def mask(mobile):
    return f"{mobile[:2]}xxxxxx{mobile[-2:]}"


def _get(user_id):
    u = USERS.get((user_id or "").strip().lower())
    if not u:
        raise AuthError("User ID not found.", 404)
    return u


# --------------------------------------------------------------------------

def login(user_id, password):
    with _lock:
        u = USERS.get((user_id or "").strip().lower())
        if not u:
            raise AuthError("Incorrect user ID or password.", 401)
        if u["locked_until"] > time.time():
            mins = int((u["locked_until"] - time.time()) // 60) + 1
            raise AuthError(f"Account locked after too many failed attempts. Try again in {mins} min or reset your password.", 423)
        if not _verify(password, u["password_hash"]):
            u["failed"] += 1
            left = MAX_FAILED - u["failed"]
            if left <= 0:
                u["failed"], u["locked_until"] = 0, time.time() + LOCK_MINUTES * 60
                _save()
                raise AuthError(f"Account locked for {LOCK_MINUTES} minutes after {MAX_FAILED} failed attempts.", 423)
            _save()
            raise AuthError(f"Incorrect user ID or password. {left} attempt(s) left.", 401)
        u["failed"], u["locked_until"] = 0, 0
        _save()
        token = secrets.token_urlsafe(32)
        _sync_sessions(add={_th(token): {"user_id": u["user_id"].lower(), "expires": time.time() + SESSION_HOURS * 3600}})
        return token, public(u)


def user_for_token(token):
    key = _th(token)
    s = SESSIONS.get(key)
    if not s and token:
        SESSIONS.update(data.read_json(SESSIONS_FILE, {}))  # maybe created by the other app
        s = SESSIONS.get(key)
    if not s or s["expires"] < time.time():
        if s:
            _sync_sessions(remove=[key])
        return None
    return USERS.get(s["user_id"])


def logout(token):
    _sync_sessions(remove=[_th(token)])


def register(farmer_id, mobile, password, confirm):
    """Farmers sign up with their Farmer ID; the mobile number must match the department record."""
    farmer_id = (farmer_id or "").strip().upper()
    f = data.FARMER_INDEX.get(farmer_id)
    if not f:
        raise AuthError("Farmer ID not found in department records.", 404)
    if (mobile or "").strip() != f["mobile"]:
        raise AuthError("Mobile number does not match the one registered with the department.")
    if farmer_id.lower() in USERS:
        raise AuthError("An account already exists for this Farmer ID. Use Login or Forgot password.", 409)
    if password != confirm:
        raise AuthError("Passwords do not match.")
    check_strength(password)
    with _lock:
        return public(_create({"user_id": farmer_id, "role": "farmer", "farmer_id": farmer_id, "password": password}))


def forgot_password(user_id):
    u = _get(user_id)
    code = f"{secrets.randbelow(1_000_000):06d}"
    OTPS[u["user_id"].lower()] = {"code_hash": _hash(code), "expires": time.time() + OTP_MINUTES * 60, "attempts": 0}
    print(f"[demo SMS] OTP for {u['user_id']} to {mask(u['mobile'])}: {code}")
    return {"sent_to": mask(u["mobile"]), "expires_in_minutes": OTP_MINUTES,
            "demo_otp": code}  # a real system would send this by SMS/email and never return it


def reset_password(user_id, otp, password, confirm):
    u = _get(user_id)
    rec = OTPS.get(u["user_id"].lower())
    if not rec or rec["expires"] < time.time():
        raise AuthError("The code has expired or was not requested. Request a new one.")
    rec["attempts"] += 1
    if rec["attempts"] > 5:
        OTPS.pop(u["user_id"].lower(), None)
        raise AuthError("Too many wrong codes. Request a new one.")
    if not _verify((otp or "").strip(), rec["code_hash"]):
        raise AuthError("Incorrect code.")
    if password != confirm:
        raise AuthError("Passwords do not match.")
    check_strength(password)
    with _lock:
        u["password_hash"] = _hash(password)
        u["failed"], u["locked_until"] = 0, 0
        _save()
    OTPS.pop(u["user_id"].lower(), None)
    # Sign out every existing session for this user
    _sync_sessions()
    _sync_sessions(remove=[k for k, s in SESSIONS.items() if s["user_id"] == u["user_id"].lower()])


def change_password(user, current, password, confirm):
    if not _verify(current or "", user["password_hash"]):
        raise AuthError("Current password is incorrect.")
    if password != confirm:
        raise AuthError("Passwords do not match.")
    if current == password:
        raise AuthError("New password must be different from the current one.")
    check_strength(password)
    with _lock:
        user["password_hash"] = _hash(password)
        _save()


def set_farmer_name(farmer_id, name):
    """Called when a farmer edits their profile so the header shows the new name."""
    with _lock:
        changed = False
        for u in USERS.values():
            if u.get("farmer_id") == farmer_id and u["name"] != name:
                u["name"] = name
                changed = True
        if changed:
            _save()


_load()
