"""Farmer consent: what the app keeps about a farmer, and their "I agree".

Every farmer sees the consent screen once, before using the app (a farmer who just
signed up sees it before filling in their details). The answer is saved to
backend/consent.json, shared by the web app and the Streamlit app. If the wording
changes in a way farmers must agree to again, raise VERSION.
"""
from pathlib import Path

from . import data

CONSENT_FILE = Path(__file__).resolve().parents[1] / "consent.json"
VERSION = 1

# The screen, in Telugu and English. Short lines for farmers who find reading hard.
TEXT = {
    "te": {
        "title": "మీ సమాచారం — మీ అనుమతి",
        "intro": "రైతు మిత్ర మీకు సహాయం చేయడానికి ఈ సమాచారాన్ని ఉంచుకుంటుంది:",
        "keeps": [
            ("👤", "మీ పేరు, గ్రామం, మొబైల్, బ్యాంక్ ఖాతా (వ్యవసాయ శాఖ రికార్డుల నుండి)"),
            ("🗺️", "మీ భూమి, పంటలు, విత్తిన / కోత తేదీలు"),
            ("📷", "మీరు పంపే పంట ఫోటోలు, వీడియోలు"),
            ("💬", "చాట్‌లో మీరు అడిగే ప్రశ్నలు"),
        ],
        "use_title": "దేనికోసం వాడతాము",
        "uses": [
            "పంట సలహా, వాతావరణం, తెగుళ్ల మందుల సలహా ఇవ్వడానికి",
            "మీ పథకాల దరఖాస్తులు, డబ్బు జమ, ఫిర్యాదుల స్థితి చూపించడానికి",
        ],
        "promise": [
            "మీ సమాచారాన్ని ప్రైవేట్ కంపెనీలకు అమ్మము, ఇవ్వము.",
            "మీకు సహాయం చేయడానికి వ్యవసాయ శాఖ అధికారులు (AEO) మాత్రమే చూడగలరు.",
            "మీ సమాచారం చూడాలన్నా, మార్చాలన్నా, తీసేయాలన్నా రైతు వేదికలో మీ AEO ని అడగండి.",
        ],
        "agree": "నేను అంగీకరిస్తున్నాను",
        "decline": "వద్దు",
        "declined": "అనుమతి ఇవ్వకుండా యాప్ వాడలేరు. సందేహాలుంటే రైతు వేదికలో మీ AEO ని అడగండి. మీకు ఇష్టమైనప్పుడు మళ్లీ లాగిన్ చేయండి.",
        "law": "డిజిటల్ వ్యక్తిగత సమాచార రక్షణ చట్టం, 2023 ప్రకారం (డెమో పాఠ్యం).",
    },
    "en": {
        "title": "Your information — your permission",
        "intro": "To help you, Rythu Mitra keeps this information:",
        "keeps": [
            ("👤", "Your name, village, mobile and bank account (from Agriculture Department records)"),
            ("🗺️", "Your land, crops, and sowing and harvest dates"),
            ("📷", "Crop photos and videos you send"),
            ("💬", "Questions you ask in the chat"),
        ],
        "use_title": "What we use it for",
        "uses": [
            "To give crop advice, weather, and medicine advice for crop problems",
            "To show your scheme applications, payments and complaints",
        ],
        "promise": [
            "We do not sell or give your information to private companies.",
            "Only Agriculture Department officers (AEO) can see it, to help you.",
            "To see, correct or delete your information, ask your AEO at the Rythu Vedika.",
        ],
        "agree": "I agree",
        "decline": "No",
        "declined": "You cannot use the app without giving permission. Ask your AEO at the Rythu Vedika if you have questions. Log in again whenever you are ready.",
        "law": "As required by the Digital Personal Data Protection Act, 2023 (demo text).",
    },
}


def speech(lang):
    """The whole screen as one plain text to read aloud."""
    t = TEXT[lang]
    parts = [t["title"], t["intro"]] + [line for _, line in t["keeps"]] + [t["use_title"]] + t["uses"] + t["promise"]
    return ". ".join(p.rstrip(".") for p in parts) + "."


def given(farmer_id):
    rec = data.read_json(CONSENT_FILE, {}).get(farmer_id or "")
    return bool(rec and rec.get("version") == VERSION and rec.get("agreed"))


def record(farmer_id, agreed, lang="te"):
    """Save the farmer's answer (with the time and the language they read it in)."""
    saved = data.read_json(CONSENT_FILE, {})
    saved[farmer_id] = {"version": VERSION, "agreed": bool(agreed), "lang": lang, "at": data.now_iso()}
    data.write_json(CONSENT_FILE, saved)
