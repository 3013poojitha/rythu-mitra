"""Next crop: what each plot could grow after the present crop, and what to expect.

For every plot we look at when it becomes free (the present crop's harvest), the soil, the water
(rainfed / canal / tank / borewell), what grew there (crop rotation: a pulse after a cereal or
cotton feeds the soil; the same crop again carries its pests over) and the district weather, and
suggest crops that can be sown in that month. For the best one we give the seed and fertilizer for
the whole plot, the sowing window and the expected harvest, income, cost and profit.

All numbers are simplified demo values in the style of PJTSAU / ICAR package-of-practice tables;
a farmer should confirm with the AEO and a soil test before sowing. Wording is in Telugu and
English, so the web app and the Streamlit app say the same thing.
"""
from datetime import date, timedelta

from . import data

MONTH_TE = ["జనవరి", "ఫిబ్రవరి", "మార్చి", "ఏప్రిల్", "మే", "జూన్", "జులై", "ఆగస్టు", "సెప్టెంబర్",
            "అక్టోబర్", "నవంబర్", "డిసెంబర్"]
MONTH_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
IRRIGATED = {"Canal", "Tank", "Borewell", "Drip", "Sprinkler"}
ASSURED = {"Canal", "Tank"}  # enough water for paddy all season
LEGUMES = {"Bengal gram (Chickpea)", "Groundnut", "Red gram", "Soybean", "Green gram (Moong)", "Black gram (Urad)"}

# When the present crop is usually harvested, if the farmer has not given a date (month)
USUAL_HARVEST = {"Paddy": 11, "Cotton": 1, "Maize": 10, "Red gram": 1, "Chilli": 2, "Turmeric": 2,
                 "Soybean": 10, "Groundnut": 10}

# crop, season, sowing months, soils (good, ok), water ("rainfed" ok / "irrigated" / "assured"),
# days, seed kg per acre, fertilizer per acre (en, te), yield quintals per acre (low, high),
# price Rs per quintal, cost Rs per acre, only after (crop) or None
CROPS = [
    ("Bengal gram (Chickpea)", "Rabi", [10, 11], {"Black cotton"}, {"Red loam", "Alluvial"}, "rainfed", 100, 30,
     ("DAP 50 kg", "DAP 50 కిలోలు"), (6, 8), 5650, 14000, None),
    ("Groundnut", "Rabi", [11, 12], {"Red sandy loam", "Red loam"}, {"Alluvial"}, "irrigated", 110, 60,
     ("DAP 50 kg + Gypsum 200 kg", "DAP 50 కిలోలు + జిప్సం 200 కిలోలు"), (8, 10), 6300, 25000, None),
    ("Maize", "Rabi", [10, 11, 12, 1], {"Alluvial", "Red loam"}, {"Black cotton", "Red sandy loam"}, "irrigated", 110, 8,
     ("Urea 100 kg + DAP 50 kg + MOP 25 kg", "యూరియా 100 కిలోలు + DAP 50 కిలోలు + MOP 25 కిలోలు"), (25, 30), 2150, 22000, None),
    ("Sunflower", "Rabi", [10, 11, 12, 1], {"Black cotton", "Alluvial"}, {"Red loam"}, "irrigated", 95, 2.5,
     ("Urea 50 kg + DAP 50 kg", "యూరియా 50 కిలోలు + DAP 50 కిలోలు"), (6, 8), 7280, 16000, None),
    ("Paddy", "Rabi", [11, 12, 1], {"Alluvial", "Black cotton"}, {"Red loam"}, "assured", 125, 25,
     ("Urea 100 kg + DAP 50 kg + MOP 30 kg", "యూరియా 100 కిలోలు + DAP 50 కిలోలు + MOP 30 కిలోలు"), (22, 26), 2300, 30000, None),
    ("Jowar (Sorghum)", "Rabi", [9, 10], {"Black cotton"}, {"Red loam"}, "rainfed", 110, 4,
     ("Urea 50 kg + DAP 25 kg", "యూరియా 50 కిలోలు + DAP 25 కిలోలు"), (8, 10), 3371, 12000, None),
    ("Black gram (Urad)", "Rabi", [11, 12], {"Alluvial", "Black cotton"}, set(), "rainfed", 80, 12,
     ("DAP 25 kg", "DAP 25 కిలోలు"), (3, 4), 7400, 9000, "Paddy"),
    ("Green gram (Moong)", "Summer", [1, 2], {"Red loam", "Alluvial"}, {"Red sandy loam"}, "irrigated", 65, 7,
     ("DAP 25 kg", "DAP 25 కిలోలు"), (3, 4), 8682, 10000, None),
    ("Sesame (Gingelly)", "Summer", [1, 2], {"Red sandy loam", "Red loam"}, {"Alluvial"}, "irrigated", 85, 2,
     ("Urea 25 kg + DAP 25 kg", "యూరియా 25 కిలోలు + DAP 25 కిలోలు"), (3, 4), 9267, 11000, None),
    ("Paddy", "Kharif", [6, 7], {"Alluvial", "Black cotton"}, {"Red loam"}, "assured", 130, 25,
     ("Urea 100 kg + DAP 50 kg + MOP 30 kg", "యూరియా 100 కిలోలు + DAP 50 కిలోలు + MOP 30 కిలోలు"), (24, 28), 2300, 30000, None),
    ("Cotton", "Kharif", [6, 7], {"Black cotton"}, {"Red loam", "Red sandy loam"}, "rainfed", 160, 0.9,
     ("Urea 100 kg + DAP 50 kg + MOP 30 kg", "యూరియా 100 కిలోలు + DAP 50 కిలోలు + MOP 30 కిలోలు"), (8, 10), 7200, 30000, None),
    ("Red gram", "Kharif", [6, 7], {"Red loam", "Black cotton"}, {"Red sandy loam"}, "rainfed", 160, 5,
     ("DAP 50 kg", "DAP 50 కిలోలు"), (5, 6), 7400, 14000, None),
    ("Maize", "Kharif", [6, 7], {"Alluvial", "Red loam"}, {"Black cotton", "Red sandy loam"}, "rainfed", 105, 8,
     ("Urea 100 kg + DAP 50 kg + MOP 25 kg", "యూరియా 100 కిలోలు + DAP 50 కిలోలు + MOP 25 కిలోలు"), (22, 28), 2150, 20000, None),
    ("Soybean", "Kharif", [6, 7], {"Black cotton"}, {"Alluvial"}, "rainfed", 100, 30,
     ("DAP 75 kg", "DAP 75 కిలోలు"), (7, 9), 4700, 15000, None),
    ("Groundnut", "Kharif", [6, 7], {"Red sandy loam"}, {"Red loam"}, "rainfed", 110, 60,
     ("DAP 50 kg + Gypsum 200 kg", "DAP 50 కిలోలు + జిప్సం 200 కిలోలు"), (7, 9), 6300, 23000, None),
]
SEASON_TE = {"Rabi": "యాసంగి (రబీ)", "Summer": "వేసవి", "Kharif": "వానాకాలం (ఖరీఫ్)"}


def _rs(n):
    """Rs in the Indian way: 1,25,000."""
    n = int(round(n, -2))
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = ",".join([head[max(0, i - 2):i] for i in range(len(head), 0, -2)][::-1])
        s = f"{head},{tail}"
    return ("-" if n < 0 else "") + "₹" + s


def _free_from(p, today):
    """When the plot is free for the next crop: the present crop's harvest (or today if it is over)."""
    if p.get("harvest_by"):
        d = date.fromisoformat(p["harvest_by"])
        return max(d, today)
    m = USUAL_HARVEST.get(p["crop"])
    if not m:
        return today
    d = date(today.year, m, 15)
    if d < today - timedelta(days=45):  # this year's harvest is long past: the crop in the field now is next year's
        d = date(today.year + 1, m, 15)
    return max(d, today)


def _sow_month(free):
    """The month sowing can start: the month the plot is free, or the next one after the 20th."""
    return free.month % 12 + 1 if free.day > 20 else free.month


def for_plot(p, district, today=None):
    """Up to 3 suggestions for one plot, best first, each with its wording in te / en."""
    today = today or date.today()
    free = _free_from(p, today)
    rain = sum(w["rain_mm"] for w in data.WEATHER.get(district, [])[:5])
    out = []
    first = _sow_month(free)
    for month_try in [(first - 1 + k) % 12 + 1 for k in range(9)]:  # the first month something can be sown
        for crop, season, months, good, ok, water, days, seed, fert, (y_lo, y_hi), price, cost, after in CROPS:
            if month_try not in months or (after and after != p["crop"]) or any(s["crop"] == crop for s in out):
                continue
            soil = p["soil"]
            if soil not in good and soil not in ok:
                continue
            irrigation = p["irrigation"]
            if water == "assured" and irrigation not in ASSURED | {"Borewell"}:
                continue
            if water == "irrigated" and irrigation not in IRRIGATED:
                continue
            score = (3 if soil in good else 1) - (1 if water == "assured" and irrigation == "Borewell" else 0)
            why_en, why_te = [], []
            why_en.append(f"Suits your {soil.lower()} soil" if soil in good else f"Grows in {soil.lower()} soil")
            why_te.append(f"మీ {_soil_te(soil)} నేలకు బాగా సరిపోతుంది"
                          if soil in good else f"మీ {_soil_te(soil)} నేలలో పండుతుంది")
            if water == "rainfed" and irrigation not in IRRIGATED:
                why_en.append("needs little water - fine without irrigation")
                why_te.append("తక్కువ నీరు చాలు - వర్షాధారంగా పండుతుంది")
            elif water != "rainfed":
                why_en.append(f"your {irrigation.lower()} water is enough")
                why_te.append(f"మీ {_water_te(irrigation)} నీరు సరిపోతుంది")
            if crop in LEGUMES and p["crop"] not in LEGUMES:
                score += 2
                why_en.append(f"a pulse after {p['crop'].lower()} puts nitrogen back in the soil")
                why_te.append(f"{data.crop_te(p['crop'])} తర్వాత పప్పుధాన్యం వేస్తే నేలకు నత్రజని వస్తుంది")
            if crop == p["crop"]:
                score -= 3
                why_en.append("same crop again - pests carry over, better to change")
                why_te.append("అదే పంట మళ్లీ - తెగుళ్లు కొనసాగుతాయి, మార్చడం మంచిది")
            if after:
                score += 2
                why_en.append("grows on the moisture left after paddy")
                why_te.append("వరి కోత తర్వాత మిగిలిన తేమతో పండుతుంది")
            acres = p["area_acres"]
            profit_lo, profit_hi = (y_lo * price - cost) * acres, (y_hi * price - cost) * acres
            sow_from = free if month_try == free.month else date(free.year + (month_try < free.month), month_try, 1)
            mid_profit = ((y_lo + y_hi) / 2 * price - cost)  # per acre
            sow_to_m = months[-1]
            harvest = sow_from + timedelta(days=days)
            out.append({
                "crop": crop, "icon": data.crop_icon(crop), "score": score + mid_profit / 15000,
                "season": season, "profit_hi": profit_hi, "sow_from": sow_from.isoformat(),
                "te": {
                    "name": data.crop_te(crop),
                    "season": SEASON_TE[season],
                    "why": why_te,
                    "sow": f"{sow_from.day} {MONTH_TE[sow_from.month - 1]} నుండి {MONTH_TE[sow_to_m - 1]} చివరి వరకు విత్తవచ్చు",
                    "seed": f"విత్తనం: {seed * acres:g} కిలోలు ({acres:g} ఎకరాలకు)",
                    "fert": f"ఎరువు: ఎకరానికి {fert[1]}",
                    "harvest": f"{days} రోజుల పంట — {MONTH_TE[harvest.month - 1]} లో కోత",
                    "yield": f"దిగుబడి: {y_lo * acres:g}–{y_hi * acres:g} క్వింటాళ్లు",
                    "money": f"ఆదాయం {_rs(y_lo * price * acres)}–{_rs(y_hi * price * acres)} · ఖర్చు {_rs(cost * acres)} · "
                             f"లాభం {_rs(profit_lo)}–{_rs(profit_hi)}",
                    "short": f"{data.crop_te(crop)} — లాభం {_rs(profit_lo)}–{_rs(profit_hi)}",
                },
                "en": {
                    "name": crop,
                    "season": f"{season} season",
                    "why": why_en,
                    "sow": f"Sow from {sow_from.day} {MONTH_EN[sow_from.month - 1]} to the end of {MONTH_EN[sow_to_m - 1]}",
                    "seed": f"Seed: {seed * acres:g} kg (for {acres:g} acres)",
                    "fert": f"Fertilizer: {fert[0]} per acre",
                    "harvest": f"{days}-day crop — harvest in {MONTH_EN[harvest.month - 1]}",
                    "yield": f"Harvest: {y_lo * acres:g}–{y_hi * acres:g} quintals",
                    "money": f"Income {_rs(y_lo * price * acres)}–{_rs(y_hi * price * acres)} · cost {_rs(cost * acres)} · "
                             f"profit {_rs(profit_lo)}–{_rs(profit_hi)}",
                    "short": f"{crop} — profit {_rs(profit_lo)}–{_rs(profit_hi)}",
                },
            })
        if out:
            break
    out.sort(key=lambda s: (-s["score"], -s["profit_hi"]))
    if out and (date.fromisoformat(out[0]["sow_from"]) - free).days > 45:  # a long gap before the next sowing
        out[0]["en"]["why"].append("until then, plough the field deep in summer - it kills pests and keeps rain water")
        out[0]["te"]["why"].append("అప్పటి వరకు వేసవిలో లోతు దుక్కి దున్నండి - పురుగులు చనిపోతాయి, వర్షం నీరు నిలుస్తుంది")
    if out and rain >= 30 and free <= today + timedelta(days=7):
        out[0]["en"]["why"].append(f"about {rain} mm rain is coming - sow once the field drains")
        out[0]["te"]["why"].append(f"సుమారు {rain} మి.మీ. వర్షం రానుంది - నీరు ఇంకిన తర్వాత విత్తండి")
    return free, out[:3]


SOIL_TE = {"Red loam": "ఎర్ర గరప", "Red sandy loam": "ఎర్ర ఇసుక గరప", "Alluvial": "ఒండ్రు", "Black cotton": "నల్లరేగడి"}
WATER_TE = {"Canal": "కాలువ", "Tank": "చెరువు", "Borewell": "బోరు", "Rainfed": "వర్షాధార", "Drip": "బిందు సేద్యం",
            "Sprinkler": "తుంపర సేద్యం"}


def _soil_te(s):
    return SOIL_TE.get(s, s)


def _water_te(w):
    return WATER_TE.get(w, w)


def for_farmer(farmer_id, today=None):
    """Every plot of the farmer: when it is free and the suggested next crops."""
    today = today or date.today()
    f = data.FARMER_INDEX.get(farmer_id)
    if not f:
        return []
    plots = []
    for p in f["plots"]:
        free, picks = for_plot(p, f["district"], today)
        if not picks:
            continue
        when_te = "ఇప్పుడే ఖాళీ" if free <= today else f"{p['crop'] and data.crop_te(p['crop'])} కోత తర్వాత ({free.day} {MONTH_TE[free.month - 1]})"
        when_en = "free now" if free <= today else f"after the {p['crop'].lower()} harvest ({free.day} {MONTH_EN[free.month - 1]})"
        head_te = (f"సర్వే {p['survey_no']} · {p['area_acres']:g} ఎకరాలు · {_soil_te(p['soil'])} నేల · "
                   f"{_water_te(p['irrigation'])} నీరు · {when_te}")
        head_en = (f"Survey {p['survey_no']} · {p['area_acres']:g} acres · {p['soil']} · {p['irrigation']} · {when_en}")
        plots.append({"survey_no": p["survey_no"], "crop": p["crop"], "free_from": free.isoformat(), "picks": picks,
                      "te": {"head": head_te, "now": f"ఇప్పుడు: {data.crop_te(p['crop'])}"},
                      "en": {"head": head_en, "now": f"Now: {p['crop']}"}})
    return plots


def speech(plots, lang):
    """All suggestions as plain text to read aloud."""
    te = lang == "te"
    parts = ["తర్వాత ఏ పంట వేయవచ్చు" if te else "What to grow next"]
    for pl in plots:
        best = pl["picks"][0][lang]
        parts += [pl[lang]["head"], pl[lang]["now"],
                  ("మంచి ఎంపిక: " if te else "Best choice: ") + best["name"], *best["why"], best["sow"], best["seed"],
                  best["fert"], best["harvest"], best["yield"], best["money"]]
        others = [p[lang]["short"] for p in pl["picks"][1:]]
        if others:
            parts.append(("ఇతర ఎంపికలు: " if te else "Other choices: ") + ", ".join(others))
    return ". ".join(x.rstrip(".") for x in parts) + "."
