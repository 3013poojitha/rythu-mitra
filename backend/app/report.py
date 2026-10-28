"""Printable farm history ("My history" -> Download / Print).

One self-contained HTML page - farmer details, crops grown season by season,
and every problem found with the remedy, whether it was used, the result and
the photos. It opens in any browser, prints cleanly on A4, and the browser's
print box can save it as a PDF. Telugu or English, like the app.
"""
import html
import re
from datetime import date, datetime

from . import data, history, seasons, terms

MONTHS_TE = ["జనవరి", "ఫిబ్రవరి", "మార్చి", "ఏప్రిల్", "మే", "జూన్", "జులై", "ఆగస్టు", "సెప్టెంబర్", "అక్టోబర్",
             "నవంబర్", "డిసెంబర్"]
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def dose_te(text):
    """'0.6 g per litre · 9.6 g per 16-L tank · 12.5 tanks' -> Telugu (amounts and units stay as on the label)."""
    text = re.sub(r"([\d.]+ \S+) per litre", r"లీటరుకు \1", text)
    text = re.sub(r"([\d.]+ \S+) per (\d+)-L tank", r"\2 లీటర్ల ట్యాంకుకు \1", text)
    text = re.sub(r"([\d.]+) tanks?", r"\1 ట్యాంకులు", text)
    return re.sub(r"([\d.]+ \S+) per acre", r"ఎకరానికి \1", text)


def build(farmer_id, lang="te"):
    """The farmer's history as one HTML page."""
    f = data.FARMER_INDEX.get((farmer_id or "").upper())
    if not f:
        raise history.HistoryError("Farmer not found.")
    te = lang == "te"
    e = html.escape

    def T(en, tel):
        return tel if te else en

    def V(value):
        return terms.te(value) if te else value

    def crop(c):
        return data.crop_te(c) if te else c

    def month(m):
        y, mm = map(int, m.split("-"))
        return f"{(MONTHS_TE if te else MONTHS_EN)[mm - 1]} {y}"

    def day(d):
        return f"{d.day} {(MONTHS_TE if te else MONTHS_EN)[d.month - 1]} {d.year}"

    district = f["district_te"] if te else f["district"]
    head = f"""
<h1>🌾 {T("Rythu Mitra — Farm history", "రైతు మిత్ర — పొలం చరిత్ర")}</h1>
<p class="sub">{T("Telangana Agriculture Dept × Bharat Vistaar", "తెలంగాణ వ్యవసాయ శాఖ × భారత్ విస్తార్")} ·
{T("Printed on", "ముద్రించిన తేదీ")} {day(date.today())}</p>
<table class="who">
<tr><th>{T("Farmer", "రైతు")}</th><td>{e(f["name"])} ({f["farmer_id"]})</td>
<th>{T("Village", "గ్రామం")}</th><td>{e(f["village"])}, {e(district)}</td></tr>
<tr><th>{T("Total land", "మొత్తం భూమి")}</th><td>{f["total_acres"]:g} {T("acres", "ఎకరాలు")}</td>
<th>{T("Crops now", "ఇప్పటి పంటలు")}</th><td>{e(", ".join(crop(c) for c in f["crops"]))}</td></tr>
</table>"""

    # Crops grown, newest first
    rows = seasons.records(f["farmer_id"])
    crop_rows = []
    for r in rows:
        until = month(r["end"]) if r["end"] else T("now (growing)", "ఇప్పటి వరకు (సాగులో)")
        if r["growing"] and r.get("expected_end"):
            until += f' · {T("harvest expected", "కోత అంచనా")} {month(r["expected_end"])}'
        harvest = f'{r["yield_qtl"]:g} {T("qtl", "క్వి.")}' if r.get("yield_qtl") is not None else "—"
        crop_rows.append(f"<tr><td>{e(r['plot'] or T('Other', 'ఇతర'))}</td><td>{e(crop(r['crop']))}</td>"
                         f"<td>{e(V(r['season']))}</td><td>{month(r['start'])} → {until}</td>"
                         f"<td>{r['area_acres']:g}</td><td>{harvest}</td></tr>")
    crops = f"""
<h2>🌱 {T("Crops grown", "సాగు చేసిన పంటలు")}</h2>
<table class="grid"><tr><th>{T("Plot", "భూమి ముక్క")}</th><th>{T("Crop", "పంట")}</th><th>{T("Season", "సీజన్")}</th>
<th>{T("From → to", "ఎప్పటి నుండి → ఎప్పటి వరకు")}</th><th>{T("Acres", "ఎకరాలు")}</th><th>{T("Harvest", "దిగుబడి")}</th></tr>
{"".join(crop_rows) or f'<tr><td colspan="6">{T("No crops recorded.", "పంటలు ఏవీ లేవు.")}</td></tr>'}</table>"""

    # Problems & remedies, newest first, with photos
    cards = []
    for r in history.records(f["farmer_id"]):
        when = datetime.fromisoformat(r["created_on"])
        fb = r["feedback"]
        remedies = "<br>".join(f'{"🌿" if m["kind"] == "Organic" else "🧪"} {e(terms.medicine(m["product"], te))}: '
                               f'{e(dose_te(m["dose"]) if te else m["dose"])} · {T("buy", "కొనాల్సింది")} {e(m["total"])}'
                               for m in r["remedies"][:2])
        if not fb:
            used, result = T("Not told yet", "ఇంకా చెప్పలేదు"), "—"
        else:
            used = V(history.USED[fb["used"]])
            if fb.get("product"):
                used += f' — {e(terms.medicine(fb["product"], te))}'
            if fb.get("reason"):
                used += f' — {e(V(fb["reason"]))}'
            if fb.get("applied_on"):
                used += f' · {T("sprayed", "పిచికారీ")} {day(date.fromisoformat(fb["applied_on"]))}'
            result = V(history.RESULTS[fb["result"]]) if fb.get("result") else "—"
        photos = []
        for kind, label in (("before", T("Before remedy", "మందుకు ముందు")), ("medicine", T("Medicine used", "వాడిన మందు")),
                            ("after", T("After remedy", "మందు తర్వాత"))):
            url = history.photo_url(r, kind)
            if url:
                photos.append(f'<figure><img src="{url}" alt="{label}"><figcaption>{label}</figcaption></figure>')
        disease = r["disease_te"] if te else r["disease"]
        cards.append(f"""<div class="case">
<h3>{day(when)} — {e(crop(r["crop"]))}{f' · {T("Plot", "భూమి ముక్క")} {e(r["plot"])}' if r.get("plot") else ""}: {e(disease)}</h3>
<table class="grid">
<tr><th>{T("Remedy given", "ఇచ్చిన మందు")}</th><td>{remedies}</td></tr>
<tr><th>{T("Used?", "వాడారా?")}</th><td>{used}</td></tr>
<tr><th>{T("Result", "ఫలితం")}</th><td>{result}{f' — “{e(fb["notes"])}”' if fb and fb.get("notes") else ""}</td></tr>
</table>{f'<div class="photos">{"".join(photos)}</div>' if photos else ""}</div>""")
    problems = f"""
<h2>🩺 {T("Problems & remedies", "సమస్యలు & నివారణలు")}</h2>
{"".join(cards) or f'<p>{T("No problems recorded.", "సమస్యలు ఏవీ నమోదు కాలేదు.")}</p>'}"""

    title = T(f"Farm history - {f['name']}", f"పొలం చరిత్ర - {f['name']}")
    return f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<style>
body {{ font-family: "Noto Sans Telugu", "Segoe UI", Arial, sans-serif; color: #1d2a1f; margin: 24px; font-size: 14px; }}
h1 {{ color: #145c2c; margin: 0 0 4px; font-size: 22px; }}
h2 {{ color: #145c2c; border-bottom: 2px solid #1f7a3e; padding-bottom: 4px; margin-top: 28px; font-size: 18px; }}
h3 {{ font-size: 15px; margin: 0 0 8px; }}
.sub {{ color: #5b675d; margin: 0 0 16px; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #cfd8cf; padding: 6px 8px; text-align: left; vertical-align: top; }}
th {{ background: #eef6ef; }}
.who th {{ width: 16%; }}
.case {{ border: 1px solid #cfd8cf; border-radius: 8px; padding: 12px; margin: 12px 0; page-break-inside: avoid; }}
.case th {{ width: 22%; }}
.photos {{ display: flex; gap: 10px; margin-top: 10px; flex-wrap: wrap; }}
figure {{ margin: 0; }}
figure img {{ width: 150px; height: 110px; object-fit: cover; border-radius: 6px; border: 1px solid #cfd8cf; }}
figcaption {{ font-size: 12px; color: #5b675d; }}
@page {{ size: A4; margin: 14mm; }}
@media print {{ body {{ margin: 0; }} }}
</style></head><body>{head}{crops}{problems}
<p class="sub" style="margin-top:24px">{T("Prototype with dummy data.", "నమూనా సమాచారంతో ప్రయోగాత్మక యాప్.")}</p>
</body></html>"""
