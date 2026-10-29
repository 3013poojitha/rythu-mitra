"""Today's update for a farmer: the pop-up that opens after the first login of the day.

In a few short lines it says what to do (or not do) on the farm today:
* today's weather,
* watering - skip it when rain is coming,
* spraying - not before rain (it washes the medicine off),
* crop work due now (fertilizer, weeding, pest watch, harvest), worked out from
  each plot's sowing and harvest dates in My Details.

Every line comes in English and Telugu. The crop calendar below is a simple demo
schedule, not official department advice.

The pop-up opens by itself once a day: the day it was last shown is kept per
farmer in backend/today_seen.json (shared by the web app and the Streamlit app).
"""
import unicodedata
from datetime import date
from pathlib import Path

from . import data

SEEN_FILE = Path(__file__).resolve().parents[1] / "today_seen.json"
RAIN_MM = 5        # this much rain or more counts as a rainy day
HOT_C = 34         # a day this hot needs watering in the morning or evening
SOON_DAYS = 3      # crop work starting within this many days is shown as "coming up"
HARVEST_DAYS = 10  # harvest reminders start this many days before the harvest date

# Crop calendar (demo): days after sowing -> work to do. (from_day, to_day, icon, English, Telugu)
GENERIC = [
    (0, 10, "💧", "Keep the soil moist so the seeds come up well.", "విత్తనాలు బాగా మొలకెత్తేలా నేల తడిగా ఉంచండి."),
    (20, 30, "🌿", "Remove weeds from the field.", "పొలంలో కలుపు తీయండి."),
    (25, 35, "🧂", "Time for the first top dose of fertilizer (urea).", "మొదటి పై ఎరువు (యూరియా) వేసే సమయం."),
    (50, 60, "🧂", "Time for the second top dose of fertilizer.", "రెండో పై ఎరువు వేసే సమయం."),
]
CALENDAR = {
    "Paddy": [
        (0, 7, "💧", "Keep 2-3 cm of water in the field after planting.", "నాటిన తర్వాత పొలంలో 2-3 సెం.మీ. నీరు ఉంచండి."),
        (20, 25, "🧂", "Time for the first dose of urea.", "మొదటి విడత యూరియా వేసే సమయం."),
        (25, 35, "🌿", "Remove weeds from the field.", "పొలంలో కలుపు తీయండి."),
        (40, 50, "🐛", "Check for stem borer and leaf folder. Spray only if you see them.",
         "కాండం తొలుచు పురుగు, ఆకు ముడత పురుగు ఉన్నాయేమో చూడండి. కనిపిస్తేనే మందు కొట్టండి."),
        (45, 50, "🧂", "Time for the second dose of urea.", "రెండో విడత యూరియా వేసే సమయం."),
        (90, 105, "💧", "Stop watering about 10 days before harvest.", "కోతకు 10 రోజుల ముందు నీరు ఆపండి."),
    ],
    "Cotton": [
        (0, 10, "💧", "Keep the soil moist so the seeds come up well.", "విత్తనాలు బాగా మొలకెత్తేలా నేల తడిగా ఉంచండి."),
        (20, 30, "🌿", "Remove weeds and loosen the soil around the plants.", "కలుపు తీసి మొక్కల చుట్టూ మట్టి గుల్ల చేయండి."),
        (30, 40, "🧂", "Time for the first top dose of fertilizer.", "మొదటి పై ఎరువు వేసే సమయం."),
        (45, 70, "🐛", "Check leaves for sucking pests (white fly, aphids).", "ఆకులపై రసం పీల్చే పురుగులు (తెల్లదోమ, పేనుబంక) ఉన్నాయేమో చూడండి."),
        (60, 70, "🧂", "Time for the second top dose of fertilizer.", "రెండో పై ఎరువు వేసే సమయం."),
        (90, 120, "🐛", "Check the bolls for pink bollworm.", "కాయల్లో గులాబీ రంగు పురుగు ఉందేమో చూడండి."),
    ],
    "Maize": [
        (0, 10, "💧", "Keep the soil moist so the seeds come up well.", "విత్తనాలు బాగా మొలకెత్తేలా నేల తడిగా ఉంచండి."),
        (15, 25, "🐛", "Check the leaf whorls for fall armyworm.", "సుడి ఆకుల్లో కత్తెర పురుగు ఉందేమో చూడండి."),
        (25, 30, "🧂", "Time for the first top dose of urea.", "మొదటి విడత యూరియా వేసే సమయం."),
        (45, 50, "🧂", "Time for the second dose of urea, before the tassels come.", "పూత రాకముందే రెండో విడత యూరియా వేయండి."),
        (55, 75, "💧", "Do not let the field dry while the cobs are forming.", "కంకులు తయారయ్యే సమయంలో పొలం ఎండిపోనీయకండి."),
    ],
    "Chilli": [
        (0, 10, "💧", "Water lightly every few days after planting.", "నాటిన తర్వాత కొన్ని రోజులకోసారి తేలికగా నీరు పెట్టండి."),
        (25, 35, "🧂", "Time for the first top dose of fertilizer.", "మొదటి పై ఎరువు వేసే సమయం."),
        (30, 60, "🐛", "Check for thrips and mites (curled leaves).", "తామర పురుగు, నల్లి (ముడుచుకున్న ఆకులు) ఉన్నాయేమో చూడండి."),
        (60, 70, "🧂", "Time for the second top dose of fertilizer.", "రెండో పై ఎరువు వేసే సమయం."),
    ],
    "Red gram": [
        (20, 30, "🌿", "Remove weeds from the field.", "పొలంలో కలుపు తీయండి."),
        (60, 90, "🐛", "At flowering, check for pod borer.", "పూత సమయంలో కాయ తొలుచు పురుగు ఉందేమో చూడండి."),
    ],
    "Soybean": [
        (15, 25, "🌿", "Remove weeds from the field.", "పొలంలో కలుపు తీయండి."),
        (30, 60, "🐛", "Check leaves for girdle beetle and leaf eaters.", "ఆకులు తినే పురుగులు ఉన్నాయేమో చూడండి."),
    ],
    "Groundnut": [
        (20, 30, "🌿", "Remove weeds from the field.", "పొలంలో కలుపు తీయండి."),
        (35, 45, "🧂", "Apply gypsum at flowering.", "పూత సమయంలో జిప్సం వేయండి."),
        (30, 70, "🐛", "Check for leaf miner and tikka leaf spots.", "ఆకు ముడత పురుగు, టిక్కా ఆకు మచ్చలు ఉన్నాయేమో చూడండి."),
    ],
    "Turmeric": [
        (30, 45, "🌿", "Remove weeds and add mulch.", "కలుపు తీసి ఆకులతో మల్చింగ్ చేయండి."),
        (60, 70, "🧂", "Time for a top dose of fertilizer and earthing up.", "పై ఎరువు వేసి మొక్కలకు మట్టి ఎగదోయండి."),
        (90, 100, "🧂", "Time for the second top dose and earthing up.", "రెండో పై ఎరువు వేసి మట్టి ఎగదోయండి."),
    ],
}


def _line(icon, en, te, tone="do"):
    """tone: 'do' something to do, 'wait' hold off, 'ok' all fine."""
    return {"icon": icon, "en": en, "te": te, "tone": tone}


def _weather_days(district):
    days = data.WEATHER.get(district) or []
    today = date.today().isoformat()
    start = next((i for i, d in enumerate(days) if d["date"] >= today), 0)
    return days[start:start + 2] + [None, None]


def _weather_lines(f):
    w, tom = _weather_days(f["district"])[:2]
    if not w:
        return None, []
    rain_today = w["rain_mm"] >= RAIN_MM
    rain_tom = bool(tom) and tom["rain_mm"] >= RAIN_MM
    icon = ("⛈️" if w["condition"] == "Thunderstorm" else "🌧️") if w["rain_mm"] else "☀️" if w["condition"] == "Sunny" else "⛅"
    weather = {
        "icon": icon, "max_c": w["max_c"], "min_c": w["min_c"], "rain_mm": w["rain_mm"],
        "en": f"{w['condition']}, {w['max_c']}° / {w['min_c']}°" + (f", about {w['rain_mm']} mm rain" if w["rain_mm"] else ""),
        "te": f"{w['condition_te']}, {w['max_c']}° / {w['min_c']}°" + (f", సుమారు {w['rain_mm']} మి.మీ. వర్షం" if w["rain_mm"] else ""),
        "tomorrow_en": tom and f"Tomorrow: {tom['condition']}" + (f", {tom['rain_mm']} mm rain" if tom["rain_mm"] else ""),
        "tomorrow_te": tom and f"రేపు: {tom['condition_te']}" + (f", {tom['rain_mm']} మి.మీ. వర్షం" if tom["rain_mm"] else ""),
    }
    lines = []
    if any(p["irrigation"] != "Rainfed" for p in f["plots"]):
        if rain_today:
            lines.append(_line("💧", "Do not water today - rain is coming. Water tomorrow or later, only if the soil is dry.",
                               "ఈరోజు నీరు పెట్టకండి - వర్షం వస్తుంది. రేపు లేదా తర్వాత, నేల ఎండితేనే నీరు పెట్టండి.", "wait"))
        elif rain_tom:
            lines.append(_line("💧", "Rain is expected tomorrow, so you can skip watering today.",
                               "రేపు వర్షం వచ్చే అవకాశం ఉంది, కాబట్టి ఈరోజు నీరు పెట్టకపోయినా పరవాలేదు.", "wait"))
        elif w["max_c"] >= HOT_C:
            lines.append(_line("💧", f"Hot day ({w['max_c']}°). Water in the early morning or evening, not at noon.",
                               f"ఈరోజు ఎండ ఎక్కువ ({w['max_c']}°). మధ్యాహ్నం కాదు, ఉదయం లేదా సాయంత్రం నీరు పెట్టండి.", "do"))
        else:
            lines.append(_line("💧", "No rain today. Water if the soil is dry - morning or evening is best.",
                               "ఈరోజు వర్షం లేదు. నేల ఎండి ఉంటే నీరు పెట్టండి - ఉదయం లేదా సాయంత్రం మంచిది.", "ok"))
    if rain_today or w["condition"] == "Thunderstorm":
        lines.append(_line("🧪", "Do not spray medicine today - the rain will wash it off.",
                           "ఈరోజు మందు పిచికారీ చేయకండి - వర్షానికి మందు కొట్టుకుపోతుంది.", "wait"))
    elif rain_tom:
        lines.append(_line("🧪", "If you must spray, do it this morning - rain is expected tomorrow.",
                           "మందు కొట్టాలంటే ఈరోజు ఉదయమే కొట్టండి - రేపు వర్షం వచ్చే అవకాశం ఉంది.", "do"))
    else:
        lines.append(_line("🧪", "Good day to spray if needed - in the morning or evening, not in the hot afternoon.",
                           "అవసరమైతే మందు కొట్టడానికి మంచి రోజు - ఉదయం లేదా సాయంత్రం కొట్టండి, మధ్యాహ్నం ఎండలో కాదు.", "ok"))
    return weather, lines


def _crop_lines(f):
    today = date.today()
    lines, no_dates, seen = [], [], set()
    for p in f["plots"]:
        crop = p["crop"]
        name_te = data.crop_te(crop)
        icon = data.crop_icon(crop)
        if p.get("harvest_by"):
            left = (date.fromisoformat(p["harvest_by"]) - today).days
            if 0 <= left <= HARVEST_DAYS and (crop, "harvest") not in seen:
                seen.add((crop, "harvest"))
                when_en = "today" if left == 0 else f"in {left} day{'s' if left != 1 else ''}"
                when_te = "ఈరోజే" if left == 0 else f"{left} రోజుల్లో"
                lines.append(_line("🧺", f"{icon} {crop}: harvest {when_en}. Arrange labour and bags.",
                                   f"{icon} {name_te}: {when_te} కోత. కూలీలు, సంచులు సిద్ధం చేసుకోండి."))
            elif -15 <= left < 0 and (crop, "harvest") not in seen:
                seen.add((crop, "harvest"))
                lines.append(_line("🧺", f"{icon} {crop}: the harvest date has passed. Harvest as soon as the crop is ready.",
                                   f"{icon} {name_te}: కోత తేదీ దాటింది. పంట సిద్ధమైతే వెంటనే కోయండి."))
            if left < 0:
                continue  # crop work only for crops still in the field
        if not p.get("sown_on"):
            if crop not in no_dates:
                no_dates.append(crop)
            continue
        age = (today - date.fromisoformat(p["sown_on"])).days
        if age < 0:
            continue
        for start, end, task_icon, en, te in CALENDAR.get(crop, GENERIC):
            key = (crop, en)
            if key in seen:
                continue
            if start <= age <= end:
                seen.add(key)
                lines.append(_line(task_icon, f"{icon} {crop} (day {age}): {en}", f"{icon} {name_te} ({age}వ రోజు): {te}"))
            elif 0 < start - age <= SOON_DAYS:
                seen.add(key)
                n = start - age
                lines.append(_line("📅", f"{icon} {crop}: in {n} day{'s' if n != 1 else ''} - {en[0].lower() + en[1:]}",
                                   f"{icon} {name_te}: {n} రోజుల్లో - {te}", "ok"))
    if no_dates:
        names_en = ", ".join(no_dates)
        names_te = ", ".join(data.crop_te(c) for c in no_dates)
        lines.append(_line("📝", f"Add the sowing date for {names_en} in My details to get crop reminders.",
                           f"పంట గుర్తుచేతల కోసం {names_te} విత్తిన తేదీని నా వివరాలు లో జోడించండి.", "ok"))
    return lines


def build(farmer_id):
    """Today's update for one farmer, with every line in English and Telugu."""
    f = data.FARMER_INDEX[farmer_id]
    weather, weather_lines = _weather_lines(f)
    crop_lines = _crop_lines(f)
    if not any(line["icon"] not in ("📝", "📅") for line in crop_lines):
        crop_lines.insert(0, _line("👍", "No crop work due today.", "ఈరోజు పంట పని ఏదీ లేదు.", "ok"))
    return {"date": date.today().isoformat(), "farmer_id": farmer_id, "name": f["name"],
            "district": f["district"], "district_te": f["district_te"],
            "weather": weather, "weather_lines": weather_lines, "crop_lines": crop_lines,
            "show": not seen_today(farmer_id)}


def speech(update, lang):
    """The whole update as one plain text to read aloud."""
    te = lang == "te"
    parts = [update["weather"][lang]] if update["weather"] else []
    parts += [line[lang] for line in update["weather_lines"] + update["crop_lines"]]
    text = ". ".join(part.rstrip(".") for part in parts) + "."
    # no emojis in speech (they would be read out as words)
    text = "".join(ch for ch in text if not unicodedata.category(ch).startswith("S") and ch != "️")
    return ("ఈరోజు వాతావరణం: " if te else "Today's weather: ") + text


def seen_today(farmer_id):
    return data.read_json(SEEN_FILE, {}).get(farmer_id) == date.today().isoformat()


def mark_seen(farmer_id):
    """The pop-up was shown today; it opens by itself again tomorrow."""
    seen = data.read_json(SEEN_FILE, {})
    seen[farmer_id] = date.today().isoformat()
    data.write_json(SEEN_FILE, seen)
