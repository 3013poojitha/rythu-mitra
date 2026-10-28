"""Understands a farmer's question and gathers the facts needed to answer it.

This is the "retrieval" half of the chatbot. It never invents information: it
looks the answer up in the dummy data (Stage 1 central data, Stage 2 published
State content, Stage 3 scheme APIs, Stage 4 land/crop records) and returns a
structured bundle of facts. An AI model (mock or real) then turns those facts
into a friendly reply - see ai.py.
"""
import re

from . import data
from .pipeline import published_chunks

TELUGU = re.compile(r"[ఀ-౿]")

INTENT_KEYWORDS = {
    "greeting": ["hello", " hi ", "namaste", "namaskaram", "నమస్కారం", "హలో", "help", "సహాయం"],
    "pest_diagnosis": ["pest", "insect", "disease", "holes", "spots", "worm", "curl", "yellow", "పురుగు", "తెగులు",
                       "మచ్చలు", "రంధ్రాలు", "ముడత", "spray", "పిచికారీ"],
    "mandi_price": ["price", "rate", "mandi", "market", "msp", "ధర", "రేటు", "మార్కెట్", "మండి"],
    "weather": ["weather", "rain", "temperature", "forecast", "climate", "వాతావరణం", "వర్షం", "ఉష్ణోగ్రత", "వాన"],
    "application_status": ["application", "status", "applied", "దరఖాస్తు", "స్థితి", "స్టేటస్"],
    "benefit_status": ["payment", "credited", "money", "benefit", "installment", "instalment", "received",
                       "డబ్బు", "జమ", "చెల్లింపు", "విడత"],
    "grievance": ["complaint", "grievance", "problem", "issue", "ఫిర్యాదు", "సమస్య"],
    "land_records": ["my land", "land record", "survey", "passbook", "acres", "నా భూమి", "భూమి", "సర్వే", "ఎకరాలు"],
    "crop_advisory": ["advice", "advisory", "fertilizer", "fertiliser", "urea", "sow", "seed", "irrigation", "yield",
                      "ఎరువు", "సలహా", "విత్తన", "యూరియా", "దిగుబడి", "నీరు"],
    "scheme_info": ["scheme", "yojana", "subsidy", "eligib", "apply", "insurance", "పథకం", "సబ్సిడీ", "అర్హత", "బీమా"],
}
# Order matters: earlier intents win when several match
INTENT_ORDER = ["application_status", "benefit_status", "grievance", "land_records", "pest_diagnosis",
                "mandi_price", "weather", "crop_advisory", "scheme_info", "greeting"]

PERSONAL_INTENTS = {"application_status", "benefit_status", "land_records"}


def detect_lang(text):
    return "te" if TELUGU.search(text) else "en"


def _has(q, word):
    # Whole-word match for English ("rice" must not match "price"); substring for Telugu
    if TELUGU.search(word):
        return word in q
    return re.search(r"\b" + re.escape(word) + r"\b", q) is not None


def _find_crop(q):
    for crop, aliases in data.CROP_ALIASES.items():
        if any(_has(q, a) for a in aliases):
            return crop
    return None


def _find_district(q):
    for en, te in data.DISTRICTS.items():
        if en.lower() in q or te in q:
            return en
    return None


def _find_scheme(q):
    for s in data.SCHEMES:
        if any(a in q for a in s["aliases"]):
            return s
    return None


def detect_intent(q, has_image=False):
    if has_image:
        return "pest_diagnosis"
    scores = {i: sum(1 for k in INTENT_KEYWORDS[i] if k in q) for i in INTENT_ORDER}
    # A named scheme without a status word means "tell me about the scheme"
    if _find_scheme(q) and not any(scores[i] for i in PERSONAL_INTENTS | {"grievance"}):
        return "scheme_info"
    best = max(INTENT_ORDER, key=lambda i: (scores[i], -INTENT_ORDER.index(i)))
    return best if scores[best] else "fallback"


def search_state_content(q, limit=2):
    """Keyword search over chunks of documents published through the pipeline (Stage 2)."""
    words = {w for w in re.findall(r"[\wఀ-౿]{4,}", q.lower())} - STOPWORDS
    hits = []
    for doc, chunk in published_chunks():
        # The whole document (Telugu original + English) must match, then the best chunk is chosen
        doc_text = (doc["raw_text"] + " " + (doc["translation"] or "") + " " + doc["title"]).lower()
        doc_score = sum(1 for w in words if w in doc_text)
        if doc_score >= 2:
            chunk_score = sum(1 for w in words if w in chunk["text"].lower())
            hits.append((doc_score, chunk_score, -chunk["id"], doc, chunk))
    hits.sort(key=lambda h: h[:3], reverse=True)
    out, seen = [], set()
    for _, cs, _, d, c in hits:
        # One chunk per document, plus a second chunk only if it matched on its own
        if d["id"] in seen and cs == 0:
            continue
        seen.add(d["id"])
        out.append({"doc_title": d["title"], "doc_id": d["id"], "text": re.sub(r"^\d+\.\s*", "", c["text"])})
        if len(out) == limit:
            break
    return out


STOPWORDS = {"what", "when", "where", "which", "does", "will", "with", "about", "from", "this", "that", "have",
             "your", "tell", "give", "today", "గురించి", "చెప్పండి", "ఏమిటి", "ఎంత"}


def gather(question, farmer_id=None, has_image=False, lang=None):
    """Return {intent, lang, stage, facts, sources, needs_login} for a question.
    lang ("te"/"en") forces the reply language (the app's language switch);
    without it the language is detected from the question."""
    q = " " + question.lower().strip() + " "
    lang = lang if lang in ("te", "en") else detect_lang(question)
    intent = detect_intent(q, has_image)
    farmer = data.FARMER_INDEX.get((farmer_id or "").upper())
    crop = _find_crop(q)
    district = _find_district(q)
    facts, sources, stage = {}, [], "Stage 1 - Central data"

    if intent in PERSONAL_INTENTS and not farmer:
        return {"intent": intent, "lang": lang, "stage": "Stage 3 - Personalised (login needed)",
                "facts": {}, "sources": [], "needs_login": True}

    if intent == "mandi_price":
        crop = crop or next((c for c in (farmer["crops"] if farmer else []) if c in data.BASE_PRICE), "Paddy")
        rows = [r for r in data.MANDI_PRICES if r["crop"] == crop]
        facts = {"crop": crop, "crop_te": data.CROPS[crop], "prices": rows, "msp": data.MSP.get(crop)}
        sources = ["Agmarknet mandi prices (dummy)"]

    elif intent == "weather":
        district = district or (farmer["district"] if farmer else "Hyderabad" if "hyderabad" in q else "Rangareddy")
        district = district if district in data.WEATHER else "Rangareddy"
        facts = {"district": district, "district_te": data.DISTRICTS[district], "forecast": data.WEATHER[district]}
        sources = ["IMD district forecast (dummy)"]

    elif intent == "scheme_info":
        scheme = _find_scheme(q)
        facts = {"scheme": scheme} if scheme else {"schemes": data.SCHEMES}
        sources = [f"{scheme['level']} scheme guidelines (dummy)" if scheme else "Scheme directory (dummy)"]
        if scheme and scheme["level"] == "State":
            stage = "Stage 2 - State content"

    elif intent in ("crop_advisory", "pest_diagnosis") and not has_image:
        crop = crop or next((c for c in (farmer["crops"] if farmer else []) if c in data.ADVISORIES), None)
        if crop:
            facts = {"crop": crop, "crop_te": data.CROPS[crop], "advice": data.ADVISORIES[crop]}
            pest = next((p for p in data.PESTS if p["crop"] == crop), None)
            if intent == "pest_diagnosis" and pest:
                facts["likely_pest"] = pest
            sources = ["ICAR crop advisory (dummy)"]
        else:
            facts = {"ask_crop": True, "crops": data.CROPS}
        if farmer:
            plot = next((p for p in farmer["plots"] if p["crop"] == crop), farmer["plots"][0])
            facts["farm"] = {"district": farmer["district"], "soil": plot["soil"], "irrigation": plot["irrigation"],
                             "area_acres": plot["area_acres"], "weather_today": data.WEATHER[farmer["district"]][0]}
            stage = "Stage 4 - Deep integration (land & crop data)"
            sources.append("Land & crop records (dummy)")

    elif intent == "application_status":
        scheme = _find_scheme(q)
        apps = farmer["applications"]
        if scheme:
            apps = [a for a in apps if a["scheme_id"] == scheme["id"]] or apps
        facts = {"farmer": _farmer_brief(farmer), "applications": [_app_view(a) for a in apps]}
        stage, sources = "Stage 3 - API-based personalised service", ["Scheme application API (dummy)"]

    elif intent == "benefit_status":
        apps = [a for a in farmer["applications"] if a["amount"]]
        facts = {"farmer": _farmer_brief(farmer), "applications": [_app_view(a) for a in apps]}
        stage, sources = "Stage 3 - API-based personalised service", ["DBT benefit status API (dummy)"]

    elif intent == "grievance":
        mine = [g for g in data.GRIEVANCES if farmer and g["farmer_id"] == farmer["farmer_id"]]
        facts = {"farmer": _farmer_brief(farmer) if farmer else None, "grievances": mine,
                 "categories": data.GRIEVANCE_CATEGORIES}
        stage, sources = "Stage 3 - API-based personalised service", ["Grievance redressal API (dummy)"]

    elif intent == "land_records":
        facts = {"farmer": _farmer_brief(farmer), "plots": farmer["plots"], "total_acres": farmer["total_acres"]}
        stage, sources = "Stage 4 - Deep integration (land & crop data)", ["Bhu Bharathi land records (dummy)"]

    # Stage 2: add matching State circulars that were published through the pipeline
    state_hits = search_state_content(q)
    if state_hits and intent not in ("greeting", "land_records"):
        facts["state_content"] = state_hits
        sources += [f"State circular: {h['doc_title']}" for h in state_hits]
        if intent == "fallback" or facts.pop("ask_crop", None):
            intent = "state_content"
        if stage.startswith("Stage 1"):
            stage = "Stage 2 - State content"

    return {"intent": intent, "lang": lang, "stage": stage, "facts": facts,
            "sources": list(dict.fromkeys(sources)), "needs_login": False,
            "farmer_name": farmer["name"] if farmer else None}


def _farmer_brief(f):
    return {"farmer_id": f["farmer_id"], "name": f["name"], "district": f["district"], "village": f["village"]}


def _app_view(a):
    s = next(s for s in data.SCHEMES if s["id"] == a["scheme_id"])
    return {**a, "scheme": s["name"], "scheme_te": s["name_te"]}
