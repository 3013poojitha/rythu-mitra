"""Spray reminders: when a remedy has to be used again.

Every remedy in the disease library has a repeat rule ("Every 7 days", "Repeat after 15 days",
"Every 10 days, 2-3 times", "Rotate after 10 days", "Change lure every 3 weeks", ...). Once a farmer
tells us (🔔 bell) which medicine they used and on which day, the next spray is due that many days
later. The reminder shows in the 🔔 bell and, on the day, in the 📅 Today pop-up. "I sprayed" starts
the count again from today; it stops after the number of sprays the rule allows, when the crop is
cured, or when the farmer turns it off.

Each reminder carries its wording in Telugu and English, so the web app and the Streamlit app say
exactly the same thing.
"""
import re
from datetime import date, timedelta

from . import data, diseases, history, terms

WEEKDAY_TE = ["సోమ", "మంగళ", "బుధ", "గురు", "శుక్ర", "శని", "ఆది"]
MONTH_TE = ["జనవరి", "ఫిబ్రవరి", "మార్చి", "ఏప్రిల్", "మే", "జూన్", "జులై", "ఆగస్టు", "సెప్టెంబర్",
            "అక్టోబర్", "నవంబర్", "డిసెంబర్"]
MAX_SPRAYS = 3  # when the rule gives no number: at most this many sprays in all


def rule(repeat):
    """The repeat text of a remedy -> {"lo", "hi", "times", "rotate", "lure", "if_needed"}, or None
    when it is not repeated on a schedule ("Single application", "Do not repeat", "Maximum 2 sprays")."""
    t = (repeat or "").lower()
    if any(w in t for w in ("do not repeat", "single", "replace when", "maximum", "twice a season", "more than twice")):
        return None
    m = re.search(r"(\d+)\s*(?:-\s*(\d+))?\s*(days?|weeks?)", t)
    if m:
        lo, hi = int(m[1]), int(m[2] or m[1])
        if m[3].startswith("week"):
            lo, hi = lo * 7, hi * 7
    elif "once a week" in t or "every week" in t:
        lo = hi = 7
    else:
        return None
    times = re.search(r"(\d+)(?:\s*-\s*(\d+))?\s*times", t)
    total = 2 if "once more" in t else int(times[2] or times[1]) if times else MAX_SPRAYS
    return {"lo": lo, "hi": hi, "times": total, "rotate": "rotate" in t, "lure": "lure" in t,
            "if_needed": " if " in f" {t} "}


def _day(d, te):
    return f"{WEEKDAY_TE[d.weekday()]}, {d.day} {MONTH_TE[d.month - 1]}" if te else f"{d:%a}, {d.day} {d:%b}"


def _when(days, due, te):
    """"Today" / "Tomorrow" / "In 4 days (Sat, 8 Nov)" / "3 days late"."""
    if days < 0:
        return (f"{-days} రోజులు ఆలస్యం — వీలైనంత త్వరగా" if te else
                f"{-days} day{'s' if days < -1 else ''} late — as soon as you can")
    if days == 0:
        return "ఈరోజే" if te else "Today"
    if days == 1:
        return f"రేపు ({_day(due, te)})" if te else f"Tomorrow ({_day(due, te)})"
    return f"{days} రోజుల్లో ({_day(due, te)})" if te else f"In {days} days ({_day(due, te)})"


def _amount(v, unit):
    return f"{v / 1000:g} {'kg' if unit == 'g' else 'L'}" if unit in ("g", "ml") and v >= 1000 else f"{v:g} {unit}"


def _dose(t, te):
    """How much for one spray of the whole field."""
    tank = diseases.SPRAYER_TANK_L
    if t["per"] == "litre":
        return (f"{tank} లీటర్ల ట్యాంకుకు {_amount(t['per_tank'], t['unit'])} · {t['tanks']:g} ట్యాంకులు · "
                f"మొత్తం {_amount(t['total'], t['unit'])}" if te else
                f"{_amount(t['per_tank'], t['unit'])} per {tank}-L tank · {t['tanks']:g} tanks · "
                f"{_amount(t['total'], t['unit'])} in all")
    return (f"ఎకరానికి {_amount(t['dose'], t['unit'])} · మొత్తం {_amount(t['total'], t['unit'])}" if te else
            f"{_amount(t['dose'], t['unit'])} per acre · {_amount(t['total'], t['unit'])} in all")


def _ordinal(n):
    return f"{n}{'st' if n == 1 else 'nd' if n == 2 else 'rd' if n == 3 else 'th'}"


def for_farmer(farmer_id, today=None):
    """The farmer's spray reminders, soonest first."""
    today = today or date.today()
    out = []
    for rec in history.records(farmer_id):
        fb = rec.get("feedback") or {}
        if fb.get("used") not in ("yes", "partly") or fb.get("result") == "cured" or rec.get("reminder_off"):
            continue
        d = diseases.INDEX.get(rec["disease_id"])
        plan = {t["product"]: t for t in diseases.plan_for(d, rec["acres"])} if d else {}
        t = plan.get(fb.get("product") or "")
        r = rule(t and t["repeat"])
        sprays = rec.get("sprays") or ([fb["applied_on"]] if fb.get("applied_on") else [])
        if not r or not sprays or len(sprays) >= r["times"]:
            continue
        last = date.fromisoformat(max(sprays))
        due = last + timedelta(days=r["lo"])
        days = (due - today).days
        n = len(sprays) + 1
        other = next((p for p in plan if p != t["product"] and plan[p]["kind"] == t["kind"]), None) if r["rotate"] else None
        crop_te, crop_en = data.CROPS.get(rec["crop"], rec["crop"]), rec["crop"]
        every_te = f"{r['lo']}-{r['hi']}" if r["hi"] != r["lo"] else f"{r['lo']}"
        notes_te, notes_en = [], []
        if other:
            notes_te.append(f"ఈసారి వేరే మందు వాడండి: {terms.medicine(other, True)}")
            notes_en.append(f"Use a different medicine this time: {other}")
        if r["if_needed"]:
            notes_te.append("సమస్య ఇంకా ఉంటేనే పిచికారీ చేయండి.")
            notes_en.append("Spray only if the problem is still there.")
        out.append({
            "id": rec["id"], "crop": rec["crop"], "plot": rec.get("plot"), "product": t["product"],
            "due": due.isoformat(), "days": days, "due_now": days <= 0, "spray_no": n, "times": r["times"],
            "lure": r["lure"],
            "te": {
                "title": "ఎర మార్చాలి" if r["lure"] else "మళ్లీ పిచికారీ చేయాలి",
                "when": _when(days, due, True),
                "what": f"{crop_te} — {rec['disease_te']}",
                "medicine": terms.medicine(t["product"], True),
                "dose": "" if r["lure"] else _dose(t, True),
                "rule": (f"{every_te} రోజుల తర్వాత మరోసారి" if r["times"] == 2 else f"ప్రతి {every_te} రోజులకు")
                        + (" · ఇదే చివరి సారి" if n == r["times"] else f" · ఇది {n}వ సారి (మొత్తం {r['times']} సార్లు)"),
                "notes": notes_te,
            },
            "en": {
                "title": "Change the lure" if r["lure"] else "Spray again",
                "when": _when(days, due, False),
                "what": f"{crop_en} — {rec['disease']}",
                "medicine": t["product"],
                "dose": "" if r["lure"] else _dose(t, False),
                "rule": (f"Once more after {every_te} days" if r["times"] == 2
                         else f"Every {every_te} days") + (" · the last one" if n == r["times"] else f" · {_ordinal(n)} of {r['times']}"),
                "notes": notes_en,
            },
        })
    return sorted(out, key=lambda x: x["due"])


def due_count(farmer_id):
    """Reminders due today or late (for the 🔔 count)."""
    return sum(r["due_now"] for r in for_farmer(farmer_id))


def speech(r, lang):
    """One reminder as plain text to read aloud."""
    w = r[lang]
    return ". ".join(x for x in [w["title"], w["when"], w["what"], w["medicine"], w["dose"], w["rule"], *w["notes"]] if x)
