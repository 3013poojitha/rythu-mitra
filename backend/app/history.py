"""Crop health history: every disease found by Crop Doctor for a farmer, the
remedy we recommended, and the farmer's feedback (did they use it, did it work).

Saved to backend/crop_history.json so it survives a restart. The file is read
fresh on every call because the React and Streamlit apps both write to it.
Photos (crop before the remedy, the medicine used, crop after) are saved in backend/crop_photos/.
Delete the file and the folder to clear all history.
"""
import base64
import io
import secrets
import threading
from datetime import date, datetime
from pathlib import Path

from . import data, diseases

HISTORY_FILE = Path(__file__).resolve().parents[1] / "crop_history.json"
PHOTO_DIR = Path(__file__).resolve().parents[1] / "crop_photos"
# before = the photo Crop Doctor checked; medicine = the bottle/packet used; after = the crop once the remedy was used
PHOTO_KINDS = ("before", "medicine", "after")

USED = {"yes": "Used it", "partly": "Used partly", "no": "Did not use"}
RESULTS = {"cured": "Cured", "improved": "Improved", "no_change": "No change", "worse": "Got worse"}
NOT_USED_REASONS = ["Could not afford it", "Not available in the shop", "Used something else",
                    "Problem went away on its own", "Waiting to confirm with AEO", "Other"]

_lock = threading.Lock()


class HistoryError(Exception):
    pass


def options():
    return {"used": USED, "results": RESULTS, "not_used_reasons": NOT_USED_REASONS}


def _read():
    return data.read_json(HISTORY_FILE, [])


def _amount(value, unit):
    """1200 g -> 1.2 kg, 1500 ml -> 1.5 L."""
    if unit in ("g", "ml") and value >= 1000:
        return f"{value / 1000:g} {'kg' if unit == 'g' else 'L'}"
    return f"{value:g} {unit}"


def _remedy(row):
    """One line a farmer can follow: product, dose and how much to buy."""
    if row["per"] == "litre":
        dose = (f"{row['dose']:g} {row['unit']} per litre · {row['per_tank']:g} {row['unit']} per "
                f"{diseases.SPRAYER_TANK_L}-L tank · {row['tanks']:g} tanks")
    else:
        dose = f"{row['dose']:g} {row['unit']} per acre"
    return {"kind": row["kind"], "product": row["product"], "dose": dose,
            "total": _amount(row["total"], row["unit"]), "when": row["when"]}


def add(farmer_id, disease_id, confidence, acres=None, source="Crop Doctor", photo=None):
    """Save a new diagnosis for a farmer. Returns the record, or None if nothing was detected."""
    f = data.FARMER_INDEX.get((farmer_id or "").upper())
    d = diseases.INDEX.get(disease_id or "")
    if not f or not d:
        return None
    plot = next((p for p in f["plots"] if p["crop"] == d["crop"]), None)
    acres = float(acres) if acres else (plot["area_acres"] if plot else 1.0)
    now = datetime.now()
    rec = {
        "id": f"H{now:%y%m%d%H%M%S}{secrets.token_hex(2)}",
        "farmer_id": f["farmer_id"], "farmer_name": f["name"], "district": f["district"],
        "created_on": now.isoformat(timespec="seconds"),
        "crop": d["crop"], "plot": plot["survey_no"] if plot else None, "acres": round(acres, 2),
        "disease_id": d["id"], "disease": d["name"], "disease_te": d["name_te"], "type": d["type"],
        "confidence": confidence, "source": source,
        "remedies": [_remedy(r) for r in diseases.plan_for(d, acres)],
        "feedback": None, "photos": {},
    }
    with _lock:
        rows = _read()
        rows.append(rec)
        data.write_json(HISTORY_FILE, rows)
    if photo:
        try:
            rec = save_photo(rec["id"], "before", photo)
        except HistoryError:
            pass  # the diagnosis is still saved without its photo
    return rec


def _shrink(image_bytes):
    """Any photo -> a JPEG of at most 800 px, so history stays small."""
    from PIL import Image, ImageOps
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("RGB")
    except Exception:
        raise HistoryError("Could not read the photo. Please send a JPG or PNG picture.")
    img.thumbnail((800, 800))
    out = io.BytesIO()
    img.save(out, "JPEG", quality=80)
    return out.getvalue()


def save_photo(record_id, kind, image_bytes, user=None):
    """Keep a crop photo with a history entry. Farmers can only add to their own entries."""
    if kind not in PHOTO_KINDS:
        raise HistoryError("Unknown photo type.")
    jpeg = _shrink(image_bytes)
    with _lock:
        rows = _read()
        rec = next((r for r in rows if r["id"] == record_id), None)
        if not rec:
            raise HistoryError("History entry not found.")
        if user and user["role"] == "farmer" and rec["farmer_id"] != user["farmer_id"]:
            raise HistoryError("You can only update your own history.")
        PHOTO_DIR.mkdir(exist_ok=True)
        name = f"{record_id}_{kind}.jpg"
        (PHOTO_DIR / name).write_bytes(jpeg)
        rec.setdefault("photos", {})[kind] = {"file": name, "on": datetime.now().isoformat(timespec="seconds")}
        data.write_json(HISTORY_FILE, rows)
    return rec


def photo_url(rec, kind):
    """The photo as a data: URL ready for an <img>, or None."""
    p = (rec.get("photos") or {}).get(kind)
    path = p and PHOTO_DIR / p["file"]
    if not path or not path.exists():
        return None
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode()


def with_photos(rows):
    """Records with their before / after photos attached, for the app screens."""
    return [{**r, "photo_urls": {k: photo_url(r, k) for k in PHOTO_KINDS}} for r in rows]


def records(farmer_id=None):
    """Newest first. farmer_id=None returns everyone's (for staff)."""
    rows = [r for r in _read() if not farmer_id or r["farmer_id"] == farmer_id]
    return sorted(rows, key=lambda r: r["created_on"], reverse=True)


def summary(rows):
    fb = [r["feedback"] for r in rows if r["feedback"]]
    used = [x for x in fb if x["used"] in ("yes", "partly")]
    worked = [x for x in used if x.get("result") in ("cured", "improved")]
    return {"cases": len(rows), "pending": len(rows) - len(fb), "used": len(used), "not_used": len(fb) - len(used),
            "worked": len(worked), "worked_pct": round(100 * len(worked) / len(used)) if used else None}


def pending_count(farmer_id):
    return sum(1 for r in records(farmer_id) if not r["feedback"])


def save_feedback(record_id, user, body):
    """Store the farmer's answer. Farmers can only answer for their own records."""
    used = body.get("used")
    if used not in USED:
        raise HistoryError("Please tell us if you used the remedy.")
    fb = {"used": used, "notes": str(body.get("notes") or "").strip()[:500],
          "updated_on": datetime.now().isoformat(timespec="seconds"), "updated_by": user["user_id"]}
    if used == "no":
        reason = body.get("reason")
        if reason not in NOT_USED_REASONS:
            raise HistoryError("Please choose why the remedy was not used.")
        fb["reason"] = reason
    else:
        if body.get("result") not in RESULTS:
            raise HistoryError("Please tell us how it worked.")
        fb["result"] = body["result"]
        fb["product"] = str(body.get("product") or "").strip()[:80] or None
        applied = body.get("applied_on")
        if applied:
            try:
                applied_d = date.fromisoformat(str(applied)[:10])
            except ValueError:
                raise HistoryError("Spray date is not a valid date.")
            if applied_d > date.today():
                raise HistoryError("Spray date cannot be in the future.")
            fb["applied_on"] = applied_d.isoformat()
    with _lock:
        rows = _read()
        rec = next((r for r in rows if r["id"] == record_id), None)
        if not rec:
            raise HistoryError("History entry not found.")
        if user["role"] == "farmer" and rec["farmer_id"] != user["farmer_id"]:
            raise HistoryError("You can only update your own history.")
        if fb.get("applied_on") and fb["applied_on"] < rec["created_on"][:10]:
            raise HistoryError("Spray date cannot be before the disease was spotted.")
        rec["feedback"] = fb
        data.write_json(HISTORY_FILE, rows)
    return rec
