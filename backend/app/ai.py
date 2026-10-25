"""AI layer: one interface, two model families (Claude and ChatGPT), two modes.

* live mode - calls the real Anthropic / OpenAI APIs (needs API keys in .env)
* mock mode - no keys, no internet, no cost. Answers are built from the same
  retrieved facts using templates, with simulated latency and token counts.
  "Claude (mock)" and "ChatGPT (mock)" write in slightly different styles so the
  side-by-side comparison screen still shows a difference.

AI_MODE=auto (the default) uses live mode for a provider whose key is set and
mock mode otherwise, so adding a key later needs no code change.
"""
import base64
import hashlib
import json
import os
import random
import time

from . import data, diseases

AI_MODE = os.getenv("AI_MODE", "auto").lower()
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

PROVIDERS = {
    "claude": {"label": "Claude", "key_env": "ANTHROPIC_API_KEY", "model": CLAUDE_MODEL},
    "gpt": {"label": "ChatGPT", "key_env": "OPENAI_API_KEY", "model": OPENAI_MODEL},
}

SYSTEM_PROMPT = (
    "You are Rythu Mitra, the Telangana Agriculture Department's assistant on the Bharat Vistaar platform. "
    "Answer farmers' questions using ONLY the facts provided in the FACTS JSON. If the facts do not contain the "
    "answer, say so and suggest contacting the local Agriculture Extension Officer (AEO) at the Rythu Vedika. "
    "Reply in the language given in LANGUAGE (te = Telugu script, en = simple English). Keep replies short, "
    "practical and respectful, using bullet points for lists. Quote prices in Rs per quintal. Never invent "
    "amounts, dates, application IDs or chemical doses that are not in the facts."
)


def is_live(provider):
    if AI_MODE == "mock":
        return False
    has_key = bool(os.getenv(PROVIDERS[provider]["key_env"]))
    return has_key if AI_MODE == "auto" else True


def status():
    return {p: {"label": v["label"], "mode": "live" if is_live(p) else "mock",
                "model": v["model"] if is_live(p) else f"{v['label']} (mock)"} for p, v in PROVIDERS.items()}


# --------------------------------------------------------------------------
# Public functions used by the API routes
# --------------------------------------------------------------------------

def answer(provider, question, gathered):
    """Turn a question + gathered facts into a reply. Returns text and metrics."""
    start = time.perf_counter()
    note = None
    if is_live(provider):
        prompt = (f"LANGUAGE: {gathered['lang']}\nINTENT: {gathered['intent']}\n"
                  f"FACTS:\n{json.dumps(gathered['facts'], ensure_ascii=False, indent=1)}\n\n"
                  f"FARMER QUESTION: {question}")
        try:
            text, tin, tout = _call_live(provider, SYSTEM_PROMPT, prompt)
            return _result(provider, text, start, tin, tout, live=True)
        except Exception as e:  # keep the demo running if the API call fails
            note = f"Live call failed ({type(e).__name__}); showing mock answer."
    text = render_mock(provider, gathered)
    res = _mock_result(provider, text, question, start)
    res["note"] = note
    return res


def translate(text, provider="claude"):
    """Telugu -> English translation for the content pipeline."""
    if is_live(provider):
        try:
            out, _, _ = _call_live(provider, "You translate Telangana agriculture documents from Telugu to clear "
                                             "English. Keep numbering, amounts and dates exactly. Output only the translation.", text)
            return out
        except Exception:
            pass
    return ("[Mock AI translation - add an API key for a real Telugu to English translation]\n\n" + text)


DIAGNOSE_PROMPT = (
    "You are a plant pathologist. Look at this crop photo{hint}. Choose the single best match from this list of "
    "disease/pest IDs, or 'healthy' if the plant looks healthy, or 'unknown' if it is not a crop photo or matches "
    "none of them:\n{options}\n\nReply ONLY with JSON: {{\"disease_id\": \"...\", \"confidence\": 0.0-1.0, "
    "\"observed\": \"one sentence on what you see in the photo, in {language}\"}}. Do not suggest chemicals or doses."
)


def diagnose(provider, image_bytes, media_type, lang="en", crop_hint=None):
    """Identify a crop disease/pest from a photo.

    The model only picks *which* problem it is. The treatment plan and doses are
    always taken from the vetted library in diseases.py, never written by the model.
    """
    start = time.perf_counter()
    pool = [d for d in diseases.DISEASES if not crop_hint or d["crop"] == crop_hint] or diseases.DISEASES
    if is_live(provider):
        options = "\n".join(f"- {d['id']}: {d['name']} on {d['crop']} ({d['type']}) - {d['symptoms']}" for d in pool)
        prompt = DIAGNOSE_PROMPT.format(hint=f" of a {crop_hint} plant" if crop_hint else "", options=options,
                                        language="Telugu" if lang == "te" else "English")
        try:
            text, tin, tout = _call_live(provider, "You identify crop diseases from photos.", prompt,
                                         image=(image_bytes, media_type))
            parsed = json.loads(text[text.find("{"): text.rfind("}") + 1])
            res = _result(provider, "", start, tin, tout, live=True)
            res["diagnosis"] = _diagnosis(parsed.get("disease_id"), float(parsed.get("confidence", 0)),
                                          parsed.get("observed"), lang)
            return res
        except Exception:
            pass
    # Mock: pick a problem from the library deterministically per image (it does not really look at the photo)
    digest = int(hashlib.md5(image_bytes).hexdigest(), 16)
    disease = pool[digest % len(pool)]
    res = _mock_result(provider, "", "image", start, base_tokens=1200)
    res["diagnosis"] = _diagnosis(disease["id"], round(0.78 + (digest % 17) / 100, 2), None, lang)
    return res


def _diagnosis(disease_id, confidence, observed, lang):
    te = lang == "te"
    d = diseases.INDEX.get(disease_id or "")
    if not d:
        healthy = disease_id == "healthy"
        return {"status": "healthy" if healthy else "unknown", "confidence": confidence, "observed": observed,
                "name": ("ఆరోగ్యంగా ఉంది" if te else "Looks healthy") if healthy else ("గుర్తించలేకపోయాం" if te else "Not recognised"),
                "crop": "", "symptoms": observed or "",
                "remedy": ("మందులు అవసరం లేదు. పర్యవేక్షణ కొనసాగించండి." if te else "No spray needed. Keep monitoring weekly.") if healthy else
                          ("స్పష్టమైన ఫోటో మళ్లీ పంపండి లేదా మీ AEO ని సంప్రదించండి." if te else "Send a clearer close-up photo of the affected leaf, or contact your AEO.")}
    return {"status": "detected", "disease_id": d["id"], "confidence": confidence, "observed": observed,
            "name": d["name_te"] if te else d["name"], "crop": data.CROPS[d["crop"]] if te else d["crop"],
            "type": d["type"], "symptoms": d["symptoms_te"] if te else d["symptoms"],
            "remedy": diseases.short_remedy(d)}


# --------------------------------------------------------------------------
# Live API calls
# --------------------------------------------------------------------------

def _call_live(provider, system, user_text, image=None):
    if provider == "claude":
        import anthropic
        client = anthropic.Anthropic()
        content = [{"type": "text", "text": user_text}]
        if image:
            content.insert(0, {"type": "image", "source": {"type": "base64", "media_type": image[1],
                                                           "data": base64.b64encode(image[0]).decode()}})
        resp = client.messages.create(model=CLAUDE_MODEL, max_tokens=4000, system=system,
                                      output_config={"effort": "low"},
                                      messages=[{"role": "user", "content": content}])
        if resp.stop_reason == "refusal":
            raise RuntimeError("refusal")
        text = "".join(b.text for b in resp.content if b.type == "text")
        return text, resp.usage.input_tokens, resp.usage.output_tokens

    from openai import OpenAI
    client = OpenAI()
    content = [{"type": "text", "text": user_text}]
    if image:
        url = f"data:{image[1]};base64,{base64.b64encode(image[0]).decode()}"
        content.append({"type": "image_url", "image_url": {"url": url}})
    resp = client.chat.completions.create(model=OPENAI_MODEL, messages=[
        {"role": "system", "content": system}, {"role": "user", "content": content}])
    return resp.choices[0].message.content, resp.usage.prompt_tokens, resp.usage.completion_tokens


def _result(provider, text, start, tin, tout, live):
    return {"provider": provider, "model": PROVIDERS[provider]["model"], "mode": "live" if live else "mock",
            "text": text, "latency_ms": int((time.perf_counter() - start) * 1000),
            "tokens_in": tin, "tokens_out": tout}


def _mock_result(provider, text, question, start, base_tokens=350):
    # Simulate a realistic delay so the UI shows its "thinking" state
    time.sleep(random.uniform(0.25, 0.7) if provider == "claude" else random.uniform(0.2, 0.55))
    res = _result(provider, text, start, base_tokens + len(question) // 3, max(40, len(text) // 3), live=False)
    res["model"] = f"{PROVIDERS[provider]['label']} (mock)"
    return res


# --------------------------------------------------------------------------
# Mock answer templates
# --------------------------------------------------------------------------

def render_mock(provider, g):
    te = g["lang"] == "te"
    title, lines, tip = _content(g, te)
    if provider == "claude":
        # Warm, explanatory style
        out = title + "\n\n" + "\n".join(f"• {l}" for l in lines)
        if tip:
            out += "\n\n" + ("💡 " + tip)
    else:
        # Short, numbered style
        out = ("**" + title + "**\n" if title else "") + "\n".join(f"{i + 1}. {l}" for i, l in enumerate(lines))
        if tip:
            out += "\n" + ("➡️ " + tip)
    if g["facts"].get("state_content") and g["intent"] != "state_content":
        h = g["facts"]["state_content"][0]
        out += ("\n\n📄 రాష్ట్ర సర్క్యులర్ నుండి: " if te else "\n\n📄 From State circular: ") + h["text"]
    return out


def _rs(n):
    return f"Rs {n:,}"


def _content(g, te):
    f, intent = g["facts"], g["intent"]
    name = g.get("farmer_name")

    if g.get("needs_login"):
        return (("ఈ సమాచారం మీ వ్యక్తిగత రికార్డుల నుండి వస్తుంది." if te else "This needs your personal records."),
                [("దయచేసి పైన మీ రైతు ID (ఉదా: TS1001) నమోదు చేయండి." if te else
                  "Please enter your Farmer ID (e.g. TS1001) at the top so I can check securely."),
                 ("మీ అనుమతితో మాత్రమే మేము రాష్ట్ర వ్యవస్థల నుండి వివరాలు తీసుకుంటాం." if te else
                  "Your details are fetched from State systems only with your consent.")], None)

    if intent == "mandi_price":
        crop = f["crop_te"] if te else f["crop"]
        lines = [f"{r['market']}: {_rs(r['modal'])} / క్వింటాల్ ({_rs(r['min'])} - {_rs(r['max'])})" if te else
                 f"{r['market']}: {_rs(r['modal'])} per quintal (range {_rs(r['min'])} - {_rs(r['max'])})"
                 for r in f["prices"]]
        best = max(f["prices"], key=lambda r: r["modal"])
        tip = None
        if f["msp"]:
            tip = (f"కనీస మద్దతు ధర (MSP): {_rs(f['msp'])} / క్వింటాల్. ఎక్కువ ధర: {best['market']}." if te else
                   f"MSP is {_rs(f['msp'])} per quintal. Best price today: {best['market']}.")
        return ((f"ఈ రోజు {crop} మార్కెట్ ధరలు:" if te else f"Today's {crop} mandi prices:"), lines, tip)

    if intent == "weather":
        dist = f["district_te"] if te else f["district"]
        lines = []
        for d in f["forecast"]:
            cond = d["condition_te"] if te else d["condition"]
            rain = (f", వర్షం {d['rain_mm']} మి.మీ." if te else f", rain {d['rain_mm']} mm") if d["rain_mm"] else ""
            lines.append(f"{d['date']}: {cond}, {d['min_c']}-{d['max_c']}°C{rain}")
        rainy = [d for d in f["forecast"] if d["rain_mm"] > 10]
        tip = (("వర్షం ఉన్న రోజుల్లో పురుగుమందులు పిచికారీ చేయవద్దు." if te else
                "Avoid spraying pesticides on rainy days; plan spraying for dry days.") if rainy else
               ("పొడి వాతావరణం - నీటి తడులు ప్లాన్ చేసుకోండి." if te else "Dry spell ahead - plan irrigation."))
        return ((f"{dist} జిల్లా 5 రోజుల వాతావరణం:" if te else f"5-day weather for {dist} district:"), lines, tip)

    if intent == "scheme_info":
        if "scheme" in f:
            s = f["scheme"]
            if te:
                return (f"{s['name_te']} ({'రాష్ట్ర' if s['level'] == 'State' else 'కేంద్ర'} పథకం)",
                        [f"లాభం: {s['benefit_te']}", f"అర్హత: {s['eligibility_te']}", f"దరఖాస్తు: {s['apply_te']}"], None)
            return (f"{s['name']} ({s['level']} scheme)",
                    [f"Benefit: {s['benefit']}", f"Eligibility: {s['eligibility']}", f"How to apply: {s['apply']}"], None)
        return (("అందుబాటులో ఉన్న ముఖ్య పథకాలు:" if te else "Key schemes available to Telangana farmers:"),
                [f"{s['name_te'] if te else s['name']} - {s['benefit_te'] if te else s['benefit']}" for s in f["schemes"]],
                ("ఏ పథకం గురించి మరిన్ని వివరాలు కావాలో అడగండి." if te else "Ask me about any scheme for details."))

    if intent in ("crop_advisory", "pest_diagnosis"):
        if f.get("ask_crop"):
            return (("మీరు ఏ పంట సాగు చేస్తున్నారు?" if te else "Which crop are you growing?"),
                    [", ".join(f["crops"].values()) if te else ", ".join(f["crops"])],
                    ("లేదా పురుగు/తెగులు ఫోటోను అప్‌లోడ్ చేయండి 📷" if te else "Or upload a photo of the affected plant 📷"))
        crop = f["crop_te"] if te else f["crop"]
        lines = list(f["advice"]["te" if te else "en"])
        title = f"{crop} పంటకు సలహాలు:" if te else f"Advisory for {crop}:"
        if f.get("likely_pest"):
            p = f["likely_pest"]
            title = (f"{crop}లో ఇది {p['name_te']} కావచ్చు." if te else f"This could be {p['name']} in {crop}.")
            lines = [p["symptoms_te"] if te else p["symptoms"], p["remedy_te"] if te else p["remedy"]] + lines[:2]
        tip = None
        if f.get("farm"):
            fm = f["farm"]
            w = fm["weather_today"]
            tip = (f"{name} గారూ, మీ {fm['area_acres']} ఎకరాల {fm['soil']} నేల, {fm['irrigation']} సాగునీరు ఆధారంగా ఈ సలహా. "
                   f"ఈ రోజు వాతావరణం: {w['condition_te']}." if te else
                   f"{name}, this is tailored to your {fm['area_acres']} acres of {fm['soil']} soil with {fm['irrigation']} "
                   f"irrigation in {fm['district']}. Today's weather: {w['condition']}.")
        return title, lines, tip

    if intent in ("application_status", "benefit_status"):
        lines = []
        for a in f["applications"]:
            amt = f" - {_rs(a['amount'])}" if a["amount"] else ""
            cred = (f", జమ తేదీ {a['credited_on']}" if te else f", credited on {a['credited_on']}") if a["credited_on"] else ""
            lines.append(f"{a['scheme_te'] if te else a['scheme']} ({a['app_id']}): {a['status']}{amt}{cred}")
        rejected = any(a["status"].startswith("Rejected") for a in f["applications"])
        tip = (("తిరస్కరించబడిన దరఖాస్తుకు భూమి రికార్డులతో AEO ని కలవండి లేదా ఫిర్యాదు నమోదు చేయండి." if te else
                "For a rejected application, visit your AEO with land records or raise a grievance here.") if rejected else None)
        return ((f"{name} గారి దరఖాస్తుల స్థితి:" if te else f"Application status for {name}:"), lines, tip)

    if intent == "grievance":
        lines = [f"{x['grievance_id']} - {x['category']}: {x['status']} ({x['created_on']})" for x in f["grievances"]]
        if not lines:
            lines = [("మీ పేరు మీద ఫిర్యాదులు లేవు." if te else "You have no grievances on record.")]
        return (("మీ ఫిర్యాదులు:" if te else "Your grievances:"), lines,
                ("కొత్త ఫిర్యాదు కోసం 'Farmer Services' ట్యాబ్‌లో నమోదు చేయండి." if te else
                 "To raise a new grievance, use the 'Farmer Services' tab - you'll get a tracking ID."))

    if intent == "land_records":
        lines = [(f"సర్వే నం. {p['survey_no']}: {p['area_acres']} ఎకరాలు, {p['soil']}, {p['irrigation']}, పంట: {data.CROPS[p['crop']]}" if te else
                  f"Survey No. {p['survey_no']}: {p['area_acres']} acres, {p['soil']} soil, {p['irrigation']}, crop: {p['crop']}")
                 for p in f["plots"]]
        return ((f"{name} గారి భూమి వివరాలు (మొత్తం {f['total_acres']} ఎకరాలు):" if te else
                 f"Land records for {name} (total {f['total_acres']} acres):"), lines, None)

    if intent == "state_content":
        return (("రాష్ట్ర వ్యవసాయ శాఖ సమాచారం ప్రకారం:" if te else "According to the State Agriculture Department:"),
                [h["text"] for h in f["state_content"]], None)

    if intent == "greeting":
        return (("నమస్కారం! నేను రైతు మిత్ర. మీకు ఎలా సహాయం చేయగలను?" if te else
                 "Namaskaram! I'm Rythu Mitra, your farming assistant."),
                (["మార్కెట్ ధరలు", "వాతావరణం", "ప్రభుత్వ పథకాలు", "పంట సలహాలు / పురుగు నివారణ", "దరఖాస్తు స్థితి"] if te else
                 ["Mandi prices", "Weather forecast", "Government schemes", "Crop advice and pest control", "Application and payment status"]),
                None)

    return (("క్షమించండి, ఈ ప్రశ్నకు నా దగ్గర సమాచారం లేదు." if te else "Sorry, I don't have information on that yet."),
            [("మార్కెట్ ధరలు, వాతావరణం, పథకాలు లేదా పంట సలహాల గురించి అడగండి." if te else
              "Try asking about mandi prices, weather, schemes or crop advice."),
             ("లేదా మీ రైతు వేదికలోని AEO ని సంప్రదించండి." if te else "Or contact the AEO at your Rythu Vedika.")], None)
