"""Crop history: which crop was grown on which plot, from which month to which.

Each entry is one crop season on one plot, e.g. Cotton on plot 393/B,
Kharif, Jun 2025 -> Nov 2025, 18 quintals. An entry with no end month is the
crop growing now.

* The first time a farmer's history is opened, a few past seasons are made up
  from the demo data (so the screen is not empty) plus one "growing now" entry
  for each plot in My Details.
* When the farmer changes a plot's crop in My Details, the old crop is closed
  (harvested this month) and the new one starts - automatically. If the farmer
  gave a sowing date, the crop starts that month; a harvest date given there is
  kept as the expected harvest month.
* Farmers can also add past crops, mark a crop harvested, edit or delete.

Saved to backend/crop_seasons.json, read fresh on every call because the React
and Streamlit apps both write to it.
"""
import random
import secrets
import threading
from datetime import date, datetime
from pathlib import Path

from . import data

SEASONS_FILE = Path(__file__).resolve().parents[1] / "crop_seasons.json"
SEASONS = ["Kharif", "Rabi", "Summer", "Both"]  # "Both" = Kharif + Rabi, same names as My Details
# Usual sowing / harvest months in Telangana, used for the made-up past seasons
WINDOWS = {"Kharif": (6, 11), "Rabi": (11, 3)}
RABI_CROPS = ["Bengal gram (Chickpea)", "Maize", "Groundnut", "Jowar (Sorghum)", "Sunflower", "Black gram (Urad)"]
YIELD_QTL_PER_ACRE = {"Paddy": 24, "Cotton": 9, "Maize": 25, "Red gram": 5, "Chilli": 20, "Turmeric": 22,
                      "Soybean": 8, "Groundnut": 8, "Bengal gram (Chickpea)": 7, "Jowar (Sorghum)": 10,
                      "Sunflower": 6, "Black gram (Urad)": 4}

_lock = threading.Lock()


class SeasonError(Exception):
    pass


def this_month():
    return date.today().strftime("%Y-%m")


def months_between(start, end=None):
    """Jun 2025 -> Nov 2025 is 6 months (both months counted)."""
    y1, m1 = map(int, start.split("-"))
    y2, m2 = map(int, (end or this_month()).split("-"))
    return (y2 - y1) * 12 + (m2 - m1) + 1


def _read():
    return data.read_json(SEASONS_FILE, {})


def _new_id():
    return f"S{datetime.now():%y%m%d%H%M%S}{secrets.token_hex(2)}"


def _current_start(season):
    """Month this season's crop was most likely sown, for crops growing now."""
    today = date.today()
    if season == "Rabi":
        y = today.year if today.month >= 10 else today.year - 1
        return f"{y}-{10 if today.month == 10 else 11}"
    y = today.year if today.month >= 6 else today.year - 1
    return f"{y}-06"


def _sown_month(p):
    """The sowing month from My Details, if one was given and it is not in the future."""
    m = (p.get("sown_on") or "")[:7]
    return m if m and m <= this_month() else None


def _harvest_month(p):
    return (p.get("harvest_by") or "")[:7] or None


def _seed(f):
    """Two years of made-up past seasons per plot + the crops growing now."""
    rng = random.Random(f["farmer_id"])
    rows = []
    year = date.today().year
    for p in f["plots"]:
        start_now = _current_start(p.get("season", "Kharif"))
        for y in (year - 2, year - 1):
            for season in ("Kharif", "Rabi"):
                s_month, e_month = WINDOWS[season]
                start = f"{y}-{s_month:02d}"
                end = f"{y + (1 if season == 'Rabi' else 0)}-{e_month:02d}"
                if end >= start_now:
                    continue
                if season == "Rabi" and p["irrigation"] == "Rainfed" and rng.random() < 0.7:
                    continue  # rainfed land is often left empty in Rabi
                crop = p["crop"] if season == "Kharif" and rng.random() < 0.7 else (
                    rng.choice(RABI_CROPS) if season == "Rabi" else rng.choice(["Cotton", "Paddy", "Maize", "Red gram"]))
                per_acre = YIELD_QTL_PER_ACRE.get(crop, 8) * rng.uniform(0.75, 1.15)
                rows.append({"id": _new_id() + str(len(rows)), "plot": p["survey_no"], "crop": crop, "season": season,
                             "start": start, "end": end, "area_acres": p["area_acres"],
                             "yield_qtl": round(per_acre * p["area_acres"], 1), "notes": "", "source": "Department records (demo)"})
        rows.append({"id": _new_id() + str(len(rows)), "plot": p["survey_no"], "crop": p["crop"],
                     "season": p.get("season", "Kharif"), "start": _sown_month(p) or start_now, "end": None,
                     "expected_end": _harvest_month(p),
                     "area_acres": p["area_acres"], "yield_qtl": None, "notes": "", "source": "My Details"})
    return rows


def _farmer(farmer_id):
    f = data.FARMER_INDEX.get((farmer_id or "").upper())
    if not f:
        raise SeasonError("Farmer not found.")
    return f


def records(farmer_id):
    """All seasons for one farmer, newest first. Creates the demo history on first use."""
    f = _farmer(farmer_id)
    with _lock:
        saved = _read()
        if f["farmer_id"] not in saved:
            saved[f["farmer_id"]] = _seed(f)
            data.write_json(SEASONS_FILE, saved)
        rows = saved[f["farmer_id"]]
    for r in rows:
        r["months"] = months_between(r["start"], r["end"])
        r["growing"] = r["end"] is None
    return sorted(rows, key=lambda r: (r["end"] is not None, r["start"]), reverse=False)[::-1] if False else \
        sorted(rows, key=lambda r: (r["end"] or "9999-99", r["start"]), reverse=True)


def options(farmer_id):
    f = _farmer(farmer_id)
    return {"seasons": SEASONS, "plots": [p["survey_no"] for p in f["plots"]], "this_month": this_month()}


def _month(value, label):
    v = str(value or "")[:7]
    try:
        datetime.strptime(v, "%Y-%m")
    except ValueError:
        raise SeasonError(f"{label}: choose a month.")
    if v > this_month():
        raise SeasonError(f"{label} cannot be in the future.")
    if v < "2000-01":
        raise SeasonError(f"{label} is too far in the past.")
    return v


def _clean(body):
    from .profiles import normalise_crop
    crop = normalise_crop(body.get("crop"))
    if not crop:
        raise SeasonError("Enter the crop name.")
    season = body.get("season") or "Kharif"
    if season not in SEASONS:
        raise SeasonError("Choose a season.")
    start = _month(body.get("start"), "Sowing month")
    end = _month(body.get("end"), "Harvest month") if body.get("end") else None
    if end and end < start:
        raise SeasonError("Harvest month cannot be before the sowing month.")
    try:
        area = round(float(body.get("area_acres")), 2)
    except (TypeError, ValueError):
        raise SeasonError("Area must be a number.")
    if not 0.1 <= area <= 100:
        raise SeasonError("Area must be between 0.1 and 100 acres.")
    yld = body.get("yield_qtl")
    if yld in ("", None) or not end:
        yld = None
    else:
        try:
            yld = round(float(yld), 1)
        except (TypeError, ValueError):
            raise SeasonError("Yield must be a number (quintals).")
        if not 0 <= yld <= 10000:
            raise SeasonError("Yield looks wrong - enter quintals for the whole area.")
    plot = str(body.get("plot") or "").strip().upper() or None
    return {"plot": plot, "crop": crop, "season": season, "start": start, "end": end, "area_acres": area,
            "yield_qtl": yld, "notes": str(body.get("notes") or "").strip()[:300]}


def add(farmer_id, body):
    f = _farmer(farmer_id)
    records(f["farmer_id"])  # make sure the demo history exists first
    row = {"id": _new_id(), **_clean(body), "source": "Added by farmer"}
    with _lock:
        saved = _read()
        saved[f["farmer_id"]].append(row)
        data.write_json(SEASONS_FILE, saved)
    return row


def update(farmer_id, season_id, body):
    f = _farmer(farmer_id)
    clean = _clean(body)
    with _lock:
        saved = _read()
        row = next((r for r in saved.get(f["farmer_id"], []) if r["id"] == season_id), None)
        if not row:
            raise SeasonError("Crop entry not found.")
        row.update(clean)
        data.write_json(SEASONS_FILE, saved)
    return row


def delete(farmer_id, season_id):
    f = _farmer(farmer_id)
    with _lock:
        saved = _read()
        rows = saved.get(f["farmer_id"], [])
        if not any(r["id"] == season_id for r in rows):
            raise SeasonError("Crop entry not found.")
        saved[f["farmer_id"]] = [r for r in rows if r["id"] != season_id]
        data.write_json(SEASONS_FILE, saved)


def sync_with_plots(farmer_id, old_plots, new_plots):
    """Called after My Details is saved: a changed or removed crop is closed
    (harvested this month); a new or changed crop starts this month."""
    with _lock:
        saved = _read()
        if farmer_id not in saved:
            return  # history not created yet; it will be seeded from the new plots
        rows = saved[farmer_id]
        old = {p["survey_no"]: p for p in old_plots}
        new = {p["survey_no"]: p for p in new_plots}
        now = this_month()
        for survey, p in old.items():
            if survey not in new or new[survey]["crop"] != p["crop"]:
                for r in rows:
                    if r["plot"] == survey and r["crop"] == p["crop"] and r["end"] is None:
                        r["end"] = now
        for survey, p in new.items():
            growing = next((r for r in rows if r["plot"] == survey and r["crop"] == p["crop"] and r["end"] is None), None)
            if growing:
                growing.update(area_acres=p["area_acres"], season=p.get("season", growing["season"]),
                               start=_sown_month(p) or growing["start"], expected_end=_harvest_month(p))
            else:
                rows.append({"id": _new_id(), "plot": survey, "crop": p["crop"], "season": p.get("season", "Kharif"),
                             "start": _sown_month(p) or now, "end": None, "expected_end": _harvest_month(p),
                             "area_acres": p["area_acres"], "yield_qtl": None, "notes": "", "source": "My Details"})
        data.write_json(SEASONS_FILE, saved)
