"""Bharat Vistaar content ingestion pipeline (proposal section 2.4).

A document moves through 11 stages. Some stages are done automatically by the
platform ("system"), others need a person in a specific role to act.
Only documents that reach "Completed" are searchable by the chatbot.
"""
import itertools
import re

from .data import now_iso

STAGES = [
    {"key": "uploaded", "label": "Uploaded", "actor": "contributor"},
    {"key": "extracting", "label": "Extracting text", "actor": "system"},
    {"key": "review_text", "label": "Review text", "actor": "reviewer"},
    {"key": "translating", "label": "Translating", "actor": "system"},
    {"key": "review_translation", "label": "Review translation", "actor": "reviewer"},
    {"key": "approve_content", "label": "Approve content", "actor": "reviewer"},
    {"key": "ready", "label": "Ready to ingest", "actor": "contributor"},
    {"key": "publish_dev", "label": "Publishing to dev", "actor": "system"},
    {"key": "approve_prod", "label": "Approve for production", "actor": "reviewer"},
    {"key": "publish_prod", "label": "Publishing to prod", "actor": "bv_central"},
    {"key": "completed", "label": "Completed", "actor": None},
]
LAST = len(STAGES) - 1

_ids = itertools.count(1)
DOCUMENTS = []


def _chunk(text):
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n(?=\d+\.)", text) if len(p.strip()) > 45]
    return [{"id": i + 1, "text": p, "approved": False} for i, p in enumerate(paras)]


def add_document(title, text, lang="te", category="Circular", translation=None, stage=0, uploaded_by="NISG Contributor"):
    doc = {
        "id": next(_ids), "title": title, "category": category, "source_lang": lang,
        "raw_text": text, "extracted_text": None, "translation": None,
        "_prepared_translation": translation, "chunks": [], "stage": 0,
        "history": [{"stage": "Uploaded", "by": uploaded_by, "at": now_iso(), "note": "Source document uploaded"}],
    }
    DOCUMENTS.append(doc)
    for _ in range(stage):
        advance(doc, by="seed")
    return doc


def advance(doc, by="user", translate_fn=None, note=None):
    """Move a document to its next stage, doing that stage's automatic work."""
    if doc["stage"] >= LAST:
        return doc
    nxt = doc["stage"] + 1
    key = STAGES[nxt]["key"]
    auto_note = note
    if key == "extracting":
        doc["extracted_text"] = doc["raw_text"]
        auto_note = auto_note or f"OCR/text extraction: {len(doc['raw_text'])} characters"
    elif key == "translating":
        if doc["source_lang"] == "en":
            doc["translation"] = doc["extracted_text"]
            auto_note = auto_note or "Source is English - translation skipped"
        elif doc["_prepared_translation"]:
            doc["translation"] = doc["_prepared_translation"]
            auto_note = auto_note or "Translated Telugu -> English"
        elif translate_fn:
            doc["translation"] = translate_fn(doc["extracted_text"])
            auto_note = auto_note or "Translated Telugu -> English by AI"
        else:
            doc["translation"] = doc["extracted_text"]
    elif key == "approve_content":
        doc["chunks"] = _chunk(doc["translation"] or doc["extracted_text"])
        auto_note = auto_note or f"AI split content into {len(doc['chunks'])} knowledge chunks"
    elif key == "ready":
        for c in doc["chunks"]:
            c["approved"] = True
    elif key == "publish_dev":
        auto_note = auto_note or "Ingested into development environment for UAT"
    elif key == "completed":
        auto_note = auto_note or "Live in production - chatbot can now answer from this document"
    doc["stage"] = nxt
    doc["history"].append({"stage": STAGES[nxt]["label"], "by": by, "at": now_iso(), "note": auto_note or ""})
    return doc


def public(doc):
    d = {k: v for k, v in doc.items() if not k.startswith("_")}
    d["stage_label"] = STAGES[doc["stage"]]["label"]
    d["next_actor"] = STAGES[doc["stage"] + 1]["actor"] if doc["stage"] < LAST else None
    d["next_label"] = STAGES[doc["stage"] + 1]["label"] if doc["stage"] < LAST else None
    return d


def published_chunks():
    for doc in DOCUMENTS:
        if doc["stage"] == LAST:
            for c in doc["chunks"]:
                yield doc, c


# --- Seed documents --------------------------------------------------------

add_document(
    "Rythu Bharosa Operational Guidelines - Rabi 2026 (dummy)",
    "రైతు భరోసా రబీ 2026 మార్గదర్శకాలు\n\n"
    "1. రబీ 2026 సీజన్‌కు ఎకరానికి రూ.6,000 పెట్టుబడి సహాయం విడుదల చేయబడుతుంది.\n\n"
    "2. సాగులో ఉన్న భూములకు మాత్రమే సహాయం వర్తిస్తుంది. రియల్ ఎస్టేట్, రోడ్లు, సాగుకు యోగ్యం కాని భూములకు వర్తించదు.\n\n"
    "3. మొదటి విడత చెల్లింపులు 2026 డిసెంబర్ 1 నుండి ప్రారంభమవుతాయి. 2 ఎకరాల లోపు రైతులకు మొదట జమ చేయబడుతుంది.\n\n"
    "4. సమస్యలుంటే రైతు వేదికలోని AEO ని సంప్రదించండి లేదా 1800-599-5959 కు కాల్ చేయండి.",
    lang="te", category="Scheme guideline",
    translation=(
        "Rythu Bharosa Rabi 2026 Guidelines\n\n"
        "1. Investment support of Rs 6,000 per acre will be released for the Rabi 2026 season.\n\n"
        "2. Support applies only to land under cultivation. It does not apply to real estate, roads or land unfit for cultivation.\n\n"
        "3. First instalment payments begin on 1 December 2026. Farmers with less than 2 acres will be paid first.\n\n"
        "4. For problems contact the AEO at the Rythu Vedika or call 1800-599-5959 (dummy helpline)."
    ),
    stage=LAST, uploaded_by="NISG Contributor",
)

add_document(
    "Paddy procurement centres - Kharif 2026 circular (dummy)",
    "Paddy Procurement - Kharif 2026\n\n"
    "1. 7,100 paddy procurement centres (PPCs) will operate across Telangana from 25 October 2026.\n\n"
    "2. Grade A paddy will be procured at MSP of Rs 2,389 per quintal plus State bonus of Rs 500 per quintal for fine varieties.\n\n"
    "3. Moisture content must be below 17%. Farmers should dry paddy before bringing it to the centre.\n\n"
    "4. Payment will be credited within 48 hours of procurement.",
    lang="en", category="Circular", stage=LAST, uploaded_by="NISG Contributor",
)

add_document(
    "Rabi 2026 seasonal crop advisory - Telangana (dummy)",
    "రబీ 2026 పంటల సలహా\n\n"
    "1. శనగ విత్తడానికి అక్టోబర్ 15 నుండి నవంబర్ 15 వరకు అనుకూల సమయం.\n\n"
    "2. వేరుశనగలో విత్తన శుద్ధి కోసం ట్రైకోడెర్మా విరిడి కిలో విత్తనానికి 10 గ్రా. వాడండి.\n\n"
    "3. నీటి ఎద్దడి ఉన్న ప్రాంతాల్లో ఆరుతడి పంటలు సాగు చేయండి.",
    lang="te", category="Advisory",
    translation=(
        "Rabi 2026 Crop Advisory\n\n"
        "1. The best time to sow Bengal gram is from 15 October to 15 November.\n\n"
        "2. For seed treatment in groundnut use Trichoderma viride at 10 g per kg of seed.\n\n"
        "3. In water-scarce areas grow irrigated dry crops."
    ),
    stage=4, uploaded_by="NISG Contributor",
)

add_document(
    "Drone spraying subsidy notification (dummy)",
    "వ్యవసాయ డ్రోన్ సబ్సిడీ\n\n"
    "1. రైతు ఉత్పత్తిదారుల సంఘాలకు (FPO) డ్రోన్ కొనుగోలుపై 75% సబ్సిడీ, గరిష్టంగా రూ.7.5 లక్షలు.\n\n"
    "2. దరఖాస్తులను జిల్లా వ్యవసాయ అధికారికి 2026 డిసెంబర్ 31 లోపు సమర్పించాలి.",
    lang="te", category="Notification", stage=1, uploaded_by="NISG Contributor",
)
