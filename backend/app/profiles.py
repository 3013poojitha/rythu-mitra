"""Farmer profile editing ("My Details").

A farmer can edit their personal details and land plots. Edits are saved to
backend/farmer_profiles.json and re-applied on top of the dummy data in data.py
every time the app starts, so they survive a restart. Delete that file to reset
every farmer back to the original demo data.

Total acres and the crop list are always worked out from the plots, so they can
never disagree with the land records.
"""
import re
import threading
from datetime import date, timedelta
from pathlib import Path

from . import data

PROFILES_FILE = Path(__file__).resolve().parents[1] / "farmer_profiles.json"
# Farmers who signed up in the app without a department Farmer ID (not yet verified by the AEO)
NEW_FARMERS_FILE = Path(__file__).resolve().parents[1] / "new_farmers.json"
NEW_ID_START = 5001  # their Farmer IDs: TS5001, TS5002, ...

SOILS = ["Black cotton", "Red sandy loam", "Alluvial", "Red loam", "Clay", "Sandy"]
IRRIGATION = ["Borewell", "Canal", "Tank", "Rainfed", "Drip", "Sprinkler"]
SEASONS = ["Kharif", "Rabi", "Both"]
GENDERS = ["Male", "Female", "Other"]
MAX_PLOTS = 10

_lock = threading.Lock()


class ProfileError(Exception):
    pass


def options():
    """Choices the edit form offers."""
    crops = [{"name": n, "te": te, "icon": icon, "group": g} for n, te, icon, g in data.CROP_CATALOG]
    return {"districts": list(data.DISTRICTS), "crops": crops, "soils": SOILS,
            "irrigation": IRRIGATION, "seasons": SEASONS, "genders": GENDERS, "max_plots": MAX_PLOTS}


def _recompute(f):
    f["total_acres"] = round(sum(p["area_acres"] for p in f["plots"]), 1)
    f["crops"] = list(dict.fromkeys(p["crop"] for p in f["plots"]))
    f["district_te"] = data.DISTRICTS[f["district"]]


def normalise_crop(text):
    """Match a typed crop to the catalogue (English, Telugu or short name, any case).
    A crop that is not in the list is still allowed, so no farmer is blocked."""
    t = " ".join(str(text or "").split())
    if not t:
        return None
    low = t.lower()
    for name, te, _, _ in data.CROP_CATALOG:
        short = name.split(" (")[0].lower()
        inside = name[name.find("(") + 1:-1].lower() if "(" in name else None
        if low in (name.lower(), short, te, inside):
            return name
    if not 2 <= len(t) <= 40 or not re.fullmatch(r"[^\W\d_][\w\s().&/-]*", t):
        return None
    return t[0].upper() + t[1:]


def _clean(changes):
    """Check the submitted values and return a clean copy, or raise ProfileError."""
    out = {}
    name = str(changes.get("name", "")).strip()
    if not 2 <= len(name) <= 60:
        raise ProfileError("Please enter your full name (2 to 60 letters).")
    out["name"] = name

    village = str(changes.get("village", "")).strip()
    if not 2 <= len(village) <= 60:
        raise ProfileError("Please enter your village name.")
    out["village"] = village

    if changes.get("district") not in data.DISTRICTS:
        raise ProfileError("Please choose a district from the list.")
    out["district"] = changes["district"]

    try:
        age = int(changes.get("age"))
    except (TypeError, ValueError):
        raise ProfileError("Age must be a number.")
    if not 18 <= age <= 100:
        raise ProfileError("Age must be between 18 and 100.")
    out["age"] = age

    if changes.get("gender") not in GENDERS:
        raise ProfileError("Please choose a gender.")
    out["gender"] = changes["gender"]

    plots = changes.get("plots") or []
    if not plots:
        raise ProfileError("Add at least one land plot.")
    if len(plots) > MAX_PLOTS:
        raise ProfileError(f"You can add up to {MAX_PLOTS} plots.")
    clean_plots, seen = [], set()
    for i, p in enumerate(plots, 1):
        survey = str(p.get("survey_no", "")).strip().upper()
        if not survey:
            raise ProfileError(f"Plot {i}: enter the survey number.")
        if survey in seen:
            raise ProfileError(f"Plot {i}: survey number {survey} is entered twice.")
        seen.add(survey)
        try:
            area = round(float(p.get("area_acres")), 2)
        except (TypeError, ValueError):
            raise ProfileError(f"Plot {i}: area must be a number.")
        if not 0.1 <= area <= 100:
            raise ProfileError(f"Plot {i}: area must be between 0.1 and 100 acres.")
        crop = normalise_crop(p.get("crop"))
        if not crop:
            raise ProfileError(f"Plot {i}: enter a crop name (letters only).")
        if p.get("soil") not in SOILS:
            raise ProfileError(f"Plot {i}: choose a soil type.")
        if p.get("irrigation") not in IRRIGATION:
            raise ProfileError(f"Plot {i}: choose a water source.")
        season = p.get("season") or "Kharif"
        if season not in SEASONS:
            raise ProfileError(f"Plot {i}: choose a season.")
        sown_on, harvest_by = _crop_dates(p, i)
        clean_plots.append({"survey_no": survey, "area_acres": area, "crop": crop, "soil": p["soil"],
                            "irrigation": p["irrigation"], "season": season,
                            "sown_on": sown_on, "harvest_by": harvest_by})
    out["plots"] = clean_plots
    return out


def _date(value, label, i):
    """An optional YYYY-MM-DD date from the form; empty means not given."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        raise ProfileError(f"Plot {i}: {label} is not a valid date.")


def _crop_dates(p, i):
    """When the crop was sown and when the harvest is expected (both optional)."""
    sown = _date(p.get("sown_on"), "sowing date", i)
    harvest = _date(p.get("harvest_by"), "harvest date", i)
    today = date.today()
    if sown and not today - timedelta(days=730) <= sown <= today + timedelta(days=180):
        raise ProfileError(f"Plot {i}: sowing date must be within the last 2 years or the next 6 months.")
    if harvest and sown and harvest <= sown:
        raise ProfileError(f"Plot {i}: harvest date must be after the sowing date.")
    if harvest and sown and harvest > sown + timedelta(days=730):
        raise ProfileError(f"Plot {i}: harvest date must be within 2 years of sowing.")
    return (sown.isoformat() if sown else None), (harvest.isoformat() if harvest else None)


def _read_file():
    return data.read_json(PROFILES_FILE, {})


def update(farmer_id, changes):
    """Validate, apply and save a farmer's edits. Returns the updated farmer record."""
    f = data.FARMER_INDEX.get((farmer_id or "").upper())
    if not f:
        raise ProfileError("Farmer not found.")
    clean = _clean(changes)
    old_plots = [dict(p) for p in f["plots"]]
    with _lock:
        f.update(clean)
        f.pop("needs_details", None)  # a new farmer has now filled their details
        _recompute(f)
        f["updated_on"] = data.now_iso()
        saved = _read_file()
        saved[f["farmer_id"]] = {**clean, "updated_on": f["updated_on"]}
        data.write_json(PROFILES_FILE, saved)
        _seen[0] = _stamp()
    # Keep the login account's display name in step with the profile
    from . import auth, seasons
    auth.set_farmer_name(f["farmer_id"], f["name"])
    # A changed crop closes the old crop season and starts a new one in Crop history
    seasons.sync_with_plots(f["farmer_id"], old_plots, f["plots"])
    return f


def mark_new(farmer_id):
    """A farmer who just signed up must fill My Details before using the app."""
    with _lock:
        saved = _read_file()
        saved[farmer_id] = {**saved.get(farmer_id, {}), "needs_details": True}
        data.write_json(PROFILES_FILE, saved)
        _seen[0] = _stamp()
        data.FARMER_INDEX[farmer_id]["needs_details"] = True


def needs_details(farmer_id):
    sync()
    return bool(data.FARMER_INDEX.get(farmer_id or "", {}).get("needs_details"))


def _mtime():
    try:
        return PROFILES_FILE.stat().st_mtime
    except FileNotFoundError:
        return None


def _stamp():
    """Modification times of both save files: if either changed, read them again."""
    try:
        new = NEW_FARMERS_FILE.stat().st_mtime
    except FileNotFoundError:
        new = None
    return _mtime(), new


_seen = [None]  # _stamp() when we last read the files


def sync():
    """Re-read the save files if they changed, e.g. an edit or a sign-up made in the other app
    (React and Streamlit run as separate programs but share these files)."""
    if _stamp() != _seen[0]:
        _load()


def _load_new_farmers():
    """Add farmers who signed up without a Farmer ID to the farmer list (once each)."""
    for rec in data.read_json(NEW_FARMERS_FILE, []):
        if rec["farmer_id"] not in data.FARMER_INDEX:
            f = dict(rec)
            data.FARMERS.append(f)
            data.FARMER_INDEX[f["farmer_id"]] = f


MOBILE = re.compile(r"[6-9]\d{9}")


def add_farmer(name, mobile, district):
    """A new farmer with no department Farmer ID signs up. Returns their new Farmer ID.
    The record is marked not verified; they fill in village, land and crops next."""
    name = " ".join(str(name or "").split())
    if not 2 <= len(name) <= 60:
        raise ProfileError("Please enter your full name (2 to 60 letters).")
    mobile = str(mobile or "").strip()
    if not MOBILE.fullmatch(mobile):
        raise ProfileError("Enter a valid 10-digit mobile number.")
    if district not in data.DISTRICTS:
        raise ProfileError("Please choose a district from the list.")
    with _lock:
        sync()
        if any(f["mobile"] == mobile for f in data.FARMERS):
            raise ProfileError("This mobile number is already in the records. Sign up with your Farmer ID, or log in.")
        n = NEW_ID_START
        while f"TS{n}" in data.FARMER_INDEX:
            n += 1
        rec = {"farmer_id": f"TS{n}", "name": name, "mobile": mobile, "district": district,
               "district_te": data.DISTRICTS[district], "village": "", "age": "", "gender": "",
               "total_acres": 0, "plots": [], "crops": [], "bank": "—", "applications": [],
               "verified": False, "registered_on": data.now_iso()}
        saved = data.read_json(NEW_FARMERS_FILE, [])
        saved.append(rec)
        data.write_json(NEW_FARMERS_FILE, saved)
        _load_new_farmers()
        _seen[0] = _stamp()
    return rec["farmer_id"]


def _load():
    _seen[0] = _stamp()
    _load_new_farmers()
    for fid, saved in _read_file().items():
        f = data.FARMER_INDEX.get(fid)
        if f:
            f.update(saved)
            f["plots"] = [{"season": "Kharif", **p} for p in f["plots"]]
            _recompute(f)


# Older dummy plots have no season; give them one so the form always has a value
for _f in data.FARMERS:
    for _p in _f["plots"]:
        _p.setdefault("season", "Kharif")
_load()
