"""FastAPI backend for the Telangana Bharat Vistaar prototype."""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")  # must run before ai.py reads env vars

from collections import Counter  # noqa: E402
from concurrent.futures import ThreadPoolExecutor  # noqa: E402
from datetime import date, timedelta  # noqa: E402
import io  # noqa: E402

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from . import ai, applications, assistant, auth, consent, data, diseases, history, media, pipeline, profiles, report, seasons, terms, today  # noqa: E402

app = FastAPI(title="Telangana Bharat Vistaar - Rythu Mitra API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
pool = ThreadPoolExecutor(max_workers=8)

# API paths that work without logging in
PUBLIC_PATHS = {"/api/status", "/api/auth/login", "/api/auth/register", "/api/auth/forgot-password",
                "/api/auth/reset-password", "/api/terms"}


def _token(request):
    header = request.headers.get("authorization", "")
    return header[7:] if header.lower().startswith("bearer ") else None


@app.middleware("http")
async def require_login(request: Request, call_next):
    path = request.url.path
    profiles.sync()  # pick up profile edits saved by the Streamlit app
    applications.sync()  # and scheme applications made there
    if path.startswith("/api/") and path not in PUBLIC_PATHS and request.method != "OPTIONS":
        user = auth.user_for_token(_token(request))
        if not user:
            return JSONResponse({"detail": "Please log in again."}, status_code=401)
        request.state.user = user
    return await call_next(request)


def _user(request):
    return request.state.user


def _staff_only(request):
    if _user(request)["role"] == "farmer":
        raise HTTPException(403, "This page is for department staff only.")


def _own_farmer_id(request, farmer_id):
    """Farmers can only see their own records; staff can look up anyone."""
    u = _user(request)
    return u["farmer_id"] if u["role"] == "farmer" else farmer_id


def _auth_call(fn, *args):
    try:
        return fn(*args)
    except auth.AuthError as e:
        raise HTTPException(e.status, str(e))


class ChatIn(BaseModel):
    message: str
    provider: str = "claude"
    farmer_id: str | None = None
    channel: str = "Web chatbot"
    lang: str | None = None  # app language switch; None = detect from the question
    log: bool = True  # False when an old reply is only redone in the other language


class CompareIn(BaseModel):
    message: str
    farmer_id: str | None = None


class ConsentIn(BaseModel):
    agree: bool
    lang: str = "te"


class ApplyIn(BaseModel):
    farmer_id: str | None = None
    scheme_id: str


class GrievanceIn(BaseModel):
    farmer_id: str
    category: str
    description: str
    channel: str = "Web chatbot"


class PlotIn(BaseModel):
    survey_no: str
    area_acres: float
    crop: str
    soil: str
    irrigation: str
    season: str = "Kharif"
    sown_on: str | None = None     # date the crop was sown (YYYY-MM-DD)
    harvest_by: str | None = None  # date the harvest is expected


class ProfileIn(BaseModel):
    name: str
    village: str
    district: str
    age: int
    gender: str
    plots: list[PlotIn]


class FeedbackIn(BaseModel):
    used: str
    product: str | None = None
    applied_on: str | None = None
    result: str | None = None
    reason: str | None = None
    notes: str | None = None


class SeasonIn(BaseModel):
    plot: str | None = None
    crop: str
    season: str = "Kharif"
    start: str
    end: str | None = None
    area_acres: float
    yield_qtl: float | None = None
    notes: str | None = None


class AdvanceIn(BaseModel):
    role: str | None = None  # only used by admins to act as another role
    note: str | None = None


class LoginIn(BaseModel):
    user_id: str
    password: str


class RegisterIn(BaseModel):
    farmer_id: str
    mobile: str
    password: str
    confirm: str


class ForgotIn(BaseModel):
    user_id: str


class ResetIn(BaseModel):
    user_id: str
    otp: str
    password: str
    confirm: str


class ChangePasswordIn(BaseModel):
    current: str
    password: str
    confirm: str


def _provider(p):
    if p not in ai.PROVIDERS:
        raise HTTPException(400, f"provider must be one of {list(ai.PROVIDERS)}")
    return p


def _log(gathered, provider, channel, farmer_id=None):
    farmer = data.FARMER_INDEX.get((farmer_id or "").upper())
    data.QUERY_HISTORY.append({
        "date": date.today().isoformat(), "intent": gathered["intent"], "lang": gathered["lang"],
        "channel": channel, "model": provider, "district": farmer["district"] if farmer else "Unknown",
        "helpful": True,
    })


@app.get("/api/terms")
def telugu_terms():
    """Telugu words for data values and common screen words (public: the login page needs them)."""
    return {"values": terms.VALUES, "ui": terms.UI, "errors": terms.ERRORS, "medicines": terms.MEDICINES}


@app.get("/api/status")
def status():
    return {"providers": ai.status(), "ai_mode_setting": ai.AI_MODE}


# ---- Login & accounts ----

@app.post("/api/auth/login")
def login(body: LoginIn):
    token, user = _auth_call(auth.login, body.user_id, body.password)
    return {"token": token, "user": user}


@app.post("/api/auth/logout")
def logout(request: Request):
    auth.logout(_token(request))
    return {"ok": True}


@app.get("/api/auth/me")
def me(request: Request):
    return auth.public(_user(request))


@app.post("/api/auth/register")
def register(body: RegisterIn):
    return _auth_call(auth.register, body.farmer_id, body.mobile, body.password, body.confirm)


@app.post("/api/auth/forgot-password")
def forgot_password(body: ForgotIn):
    return _auth_call(auth.forgot_password, body.user_id)


@app.post("/api/auth/reset-password")
def reset_password(body: ResetIn):
    _auth_call(auth.reset_password, body.user_id, body.otp, body.password, body.confirm)
    return {"ok": True}


@app.post("/api/auth/change-password")
def change_password(body: ChangePasswordIn, request: Request):
    _auth_call(auth.change_password, _user(request), body.current, body.password, body.confirm)
    return {"ok": True}


# ---- Chatbot ----

@app.post("/api/chat")
def chat(body: ChatIn, request: Request):
    provider = _provider(body.provider)
    farmer_id = _own_farmer_id(request, body.farmer_id)
    gathered = assistant.gather(body.message, farmer_id, lang=body.lang)
    res = ai.answer(provider, body.message, gathered)
    if body.log:
        _log(gathered, provider, body.channel, farmer_id)
    return {**res, "intent": gathered["intent"], "lang": gathered["lang"], "stage": gathered["stage"],
            "sources": gathered["sources"], "needs_login": gathered["needs_login"]}


@app.post("/api/compare")
def compare(body: CompareIn, request: Request):
    _staff_only(request)
    gathered = assistant.gather(body.message, body.farmer_id)
    futures = {p: pool.submit(ai.answer, p, body.message, gathered) for p in ai.PROVIDERS}
    return {"intent": gathered["intent"], "stage": gathered["stage"], "sources": gathered["sources"],
            "results": {p: f.result() for p, f in futures.items()}}


@app.post("/api/transcribe")
async def transcribe(file: UploadFile = File(...), lang: str = Form("te")):
    """A recorded voice message -> text (live mode only; mock mode returns text: null)."""
    audio = await file.read()
    if len(audio) > 10 * 1024 * 1024:
        raise HTTPException(413, "Recording too long (max 10 MB)")
    return {"text": ai.transcribe(audio, file.filename or "voice.webm", lang)}


@app.post("/api/diagnose")
async def diagnose(request: Request, files: list[UploadFile] | None = File(None), file: UploadFile | None = File(None),
                   provider: str = Form("claude"), lang: str = Form("en"), crop: str | None = Form(None),
                   acres: float | None = Form(None), source: str = Form("Crop Doctor")):
    """Any number of photos and videos of the same crop ("files"; "file" still works for one photo).
    Videos are turned into a few still frames; everything is checked together."""
    uploads = [(await f.read(), f.content_type, f.filename) for f in (files or []) + ([file] if file else [])]
    try:
        pics, counts = media.pictures(uploads)
    except media.MediaError as e:
        raise HTTPException(413 if "too large" in str(e) else 400, str(e))
    res = ai.diagnose_many(_provider(provider), media.for_ai(pics), lang, crop or None)
    data.QUERY_HISTORY.append({"date": date.today().isoformat(), "intent": "pest_diagnosis", "lang": lang,
                               "channel": "Web chatbot", "model": provider, "district": "Unknown", "helpful": True})
    # Farmers get every detected disease saved to their History, to give feedback on later
    u = _user(request)
    saved = None
    if u["role"] == "farmer" and res["diagnosis"]["status"] == "detected":
        saved = history.add(u["farmer_id"], res["diagnosis"]["disease_id"], res["diagnosis"]["confidence"],
                            acres, "Chat photo" if source == "Chat" else "Crop Doctor", photo=pics[0][0])
    both = {l: ai.diagnosis_in(res["diagnosis"], l) for l in ("te", "en")}  # follows the language switch
    return {**res, "both": both, "stage": "Image-based crop/pest diagnosis", "media": counts,
            "sources": ["Crop Doctor disease library (dummy)"], "history_id": saved and saved["id"]}


@app.get("/api/diseases")
def disease_library(acres: float = 1.0):
    """Disease library with spray quantities worked out for the given farm size."""
    acres = min(max(acres, 0.1), 100)
    return {"sprayer_tank_l": diseases.SPRAYER_TANK_L, "safety": diseases.SAFETY, "acres": acres,
            "diseases": [{**d, "plan": diseases.plan_for(d, acres), "crop_te": data.CROPS[d["crop"]]}
                         for d in diseases.DISEASES]}


# ---- Farmer services (Stage 3 / 4) ----

@app.get("/api/farmers")
def farmers(request: Request):
    own = _own_farmer_id(request, None)
    return [{k: f[k] for k in ("farmer_id", "name", "district", "village", "total_acres", "crops")}
            for f in data.FARMERS if not own or f["farmer_id"] == own]


@app.get("/api/farmers/{farmer_id}")
def farmer(farmer_id: str, request: Request):
    f = data.FARMER_INDEX.get(_own_farmer_id(request, farmer_id).upper())
    if not f:
        raise HTTPException(404, "Farmer not found")
    apps = [assistant._app_view(a) for a in f["applications"]]
    griev = [g for g in data.GRIEVANCES if g["farmer_id"] == f["farmer_id"]]
    return {**f, "applications": apps, "grievances": griev, "weather": data.WEATHER[f["district"]],
            "schemes_open": applications.open_schemes(f["farmer_id"]),  # schemes they can apply for now
            "advisories": {c: data.ADVISORIES[c] for c in f["crops"] if c in data.ADVISORIES}}


@app.get("/api/profile-options")
def profile_options():
    return profiles.options()


@app.put("/api/farmers/{farmer_id}")
def update_farmer(farmer_id: str, body: ProfileIn, request: Request):
    fid = _own_farmer_id(request, farmer_id)
    try:
        profiles.update(fid, body.model_dump())
    except profiles.ProfileError as e:
        raise HTTPException(400, str(e))
    return farmer(fid, request)


# ---- Consent (farmers agree once before using the app) ----

@app.get("/api/consent")
def consent_text():
    return {"text": consent.TEXT, "speech": {"te": consent.speech("te"), "en": consent.speech("en")},
            "version": consent.VERSION}


@app.post("/api/consent")
def consent_answer(body: ConsentIn, request: Request):
    u = _user(request)
    if u["role"] == "farmer":
        consent.record(u["farmer_id"], body.agree, body.lang)
    return auth.public(u)


# ---- Today's update (pop-up after the first login of the day) ----

@app.get("/api/today")
def today_update(request: Request, lang: str = "te"):
    u = _user(request)
    if u["role"] != "farmer":
        raise HTTPException(403, "Today's update is for farmers.")
    update = today.build(u["farmer_id"])
    update["speech"] = {"en": today.speech(update, "en"), "te": today.speech(update, "te")}
    return update


@app.post("/api/today/seen")
def today_seen(request: Request):
    u = _user(request)
    if u["role"] == "farmer":
        today.mark_seen(u["farmer_id"])
    return {"ok": True}


# ---- Crop health history (Crop Doctor follow-up) ----

@app.get("/api/history")
def crop_history(request: Request):
    u = _user(request)
    rows = history.records(u["farmer_id"] if u["role"] == "farmer" else None)
    return {"records": history.with_photos(rows), "summary": history.summary(rows), "options": history.options()}


@app.get("/api/history/report")
def history_report(request: Request, lang: str = "te", farmer_id: str | None = None):
    """My history as one printable page (download it, or print / save as PDF)."""
    fid = _own_farmer_id(request, farmer_id or "")
    if not fid:
        raise HTTPException(400, "Choose a farmer first.")
    try:
        return HTMLResponse(report.build(fid, "en" if lang == "en" else "te"))
    except history.HistoryError as e:
        raise HTTPException(404, str(e))


@app.post("/api/history/{record_id}/feedback")
def history_feedback(record_id: str, body: FeedbackIn, request: Request):
    try:
        return history.save_feedback(record_id, _user(request), body.model_dump())
    except history.HistoryError as e:
        raise HTTPException(400, str(e))


@app.post("/api/history/{record_id}/photo")
async def history_photo(record_id: str, request: Request, file: UploadFile = File(...), kind: str = Form("after")):
    """kind: 'after' (the crop once the remedy was used) or 'medicine' (the bottle/packet used).
    The 'before' photo is saved by /api/diagnose."""
    img = await file.read()
    if len(img) > 8 * 1024 * 1024:
        raise HTTPException(413, "Image too large (max 8 MB)")
    try:
        return history.save_photo(record_id, kind, img, _user(request))
    except history.HistoryError as e:
        raise HTTPException(400, str(e))


# ---- Crop history: which crop on which plot, month to month ----

def _season_call(fn, *args):
    try:
        return fn(*args)
    except seasons.SeasonError as e:
        raise HTTPException(400, str(e))


@app.get("/api/seasons/{farmer_id}")
def crop_seasons(farmer_id: str, request: Request):
    fid = _own_farmer_id(request, farmer_id)
    return {"records": _season_call(seasons.records, fid), "options": _season_call(seasons.options, fid)}


@app.post("/api/seasons/{farmer_id}")
def add_season(farmer_id: str, body: SeasonIn, request: Request):
    return _season_call(seasons.add, _own_farmer_id(request, farmer_id), body.model_dump())


@app.put("/api/seasons/{farmer_id}/{season_id}")
def edit_season(farmer_id: str, season_id: str, body: SeasonIn, request: Request):
    return _season_call(seasons.update, _own_farmer_id(request, farmer_id), season_id, body.model_dump())


@app.delete("/api/seasons/{farmer_id}/{season_id}")
def delete_season(farmer_id: str, season_id: str, request: Request):
    _season_call(seasons.delete, _own_farmer_id(request, farmer_id), season_id)
    return {"ok": True}


@app.post("/api/applications")
def apply_for_scheme(body: ApplyIn, request: Request):
    """A farmer applies for a scheme from Home; it starts as Pending verification."""
    try:
        app_ = applications.apply(_own_farmer_id(request, body.farmer_id), body.scheme_id)
    except applications.ApplicationError as e:
        raise HTTPException(400, str(e))
    return assistant._app_view(app_)


@app.get("/api/grievances")
def grievances(request: Request):
    _staff_only(request)
    return sorted(data.GRIEVANCES, key=lambda g: g["created_on"], reverse=True)


@app.post("/api/grievances")
def create_grievance(body: GrievanceIn, request: Request):
    f = data.FARMER_INDEX.get(_own_farmer_id(request, body.farmer_id).upper())
    if not f:
        raise HTTPException(404, "Farmer not found")
    g = {"grievance_id": f"GRV-{2401 + len(data.GRIEVANCES)}", "farmer_id": f["farmer_id"], "farmer_name": f["name"],
         "district": f["district"], "category": body.category, "description": body.description,
         "status": "Open", "created_on": date.today().isoformat(), "channel": body.channel}
    data.GRIEVANCES.append(g)
    return g


# ---- Content pipeline (Stage 2) ----

@app.get("/api/pipeline/stages")
def stages():
    return pipeline.STAGES


@app.get("/api/documents")
def documents(request: Request):
    _staff_only(request)
    return [pipeline.public(d) for d in reversed(pipeline.DOCUMENTS)]


@app.post("/api/documents")
async def upload_document(request: Request, title: str = Form(...), category: str = Form("Circular"),
                          lang: str = Form("te"), text: str = Form(""), file: UploadFile | None = File(None)):
    user = _user(request)
    if user["role"] not in ("contributor", "admin"):
        raise HTTPException(403, "Only a Contributor or Admin can upload documents.")
    body = text.strip()
    if file is not None and file.filename:
        raw = await file.read()
        if file.filename.lower().endswith(".pdf"):
            try:
                from pypdf import PdfReader
                body = "\n\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(raw)).pages).strip()
            except Exception:
                raise HTTPException(400, "Could not read that PDF. Paste the text instead.")
        else:
            body = raw.decode("utf-8", errors="ignore").strip()
    if not body:
        raise HTTPException(400, "Provide document text or a .txt/.pdf file")
    doc = pipeline.add_document(title, body, lang=lang, category=category, uploaded_by=user["name"])
    return pipeline.public(doc)


@app.post("/api/documents/{doc_id}/advance")
def advance(doc_id: int, body: AdvanceIn, request: Request):
    user = _user(request)
    _staff_only(request)
    # Each user acts in their own role; only an admin may act as someone else
    role = (body.role or "admin") if user["role"] == "admin" else user["role"]
    doc = next((d for d in pipeline.DOCUMENTS if d["id"] == doc_id), None)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc["stage"] >= pipeline.LAST:
        raise HTTPException(400, "Document is already published")
    actor = pipeline.STAGES[doc["stage"] + 1]["actor"]
    if role != "admin" and actor != "system" and actor != role:
        raise HTTPException(403, f"This step needs the '{auth.ROLES[actor]}' role")
    by = "Bharat Vistaar platform" if actor == "system" else f"{user['name']} ({auth.ROLES[role]})"
    pipeline.advance(doc, by=by, translate_fn=ai.translate, note=body.note)
    return pipeline.public(doc)


# ---- Reference data (Stage 1) ----

@app.get("/api/reference")
def reference():
    return {"schemes": data.SCHEMES, "mandi_prices": data.MANDI_PRICES, "weather": data.WEATHER,
            "districts": data.DISTRICTS, "crops": data.CROPS, "grievance_categories": data.GRIEVANCE_CATEGORIES}


# ---- PMU dashboard & governance ----

@app.get("/api/dashboard")
def dashboard(request: Request):
    _staff_only(request)
    rows = data.QUERY_HISTORY
    today = date.today()
    last7 = [r for r in rows if r["date"] >= (today - timedelta(days=7)).isoformat()]
    by_day = Counter(r["date"] for r in rows)
    docs = pipeline.DOCUMENTS
    return {
        "kpis": {
            "total_queries": len(rows), "queries_7d": len(last7),
            "telugu_share": round(100 * sum(r["lang"] == "te" for r in rows) / max(1, len(rows))),
            "helpful_rate": round(100 * sum(r["helpful"] for r in rows) / max(1, len(rows))),
            "farmers_onboarded": len(data.FARMERS),
            "docs_published": sum(d["stage"] == pipeline.LAST for d in docs), "docs_in_pipeline": len(docs),
            "open_grievances": sum(g["status"] != "Resolved" for g in data.GRIEVANCES),
        },
        "by_day": [{"date": d, "count": by_day[d]} for d in sorted(by_day)][-30:],
        "by_intent": Counter(r["intent"] for r in rows).most_common(),
        "by_channel": Counter(r["channel"] for r in rows).most_common(),
        "by_model": Counter(r["model"] for r in rows).most_common(),
        "by_district": Counter(r["district"] for r in rows if r["district"] != "Unknown").most_common(12),
        "tracker": data.TRACKER, "issues": data.ISSUES,
    }


@app.post("/api/evaluate")
def evaluate(request: Request):
    """Run the agreed test scenarios through both models and score them (proposal section 2.9)."""
    _staff_only(request)
    def run(sc):
        gathered = assistant.gather(sc["question"])
        out = {}
        for p in ai.PROVIDERS:
            r = ai.answer(p, sc["question"], gathered)
            text = r["text"].lower()
            hits = [k for k in sc["expect"] if k.lower() in text]
            lang_ok = (assistant.detect_lang(r["text"]) == sc["lang"]) or sc["lang"] == "en"
            out[p] = {"pass": len(hits) == len(sc["expect"]) and lang_ok, "matched": hits, "latency_ms": r["latency_ms"],
                      "tokens_out": r["tokens_out"], "text": r["text"], "model": r["model"]}
        return {**sc, "intent": gathered["intent"], "results": out}

    results = list(pool.map(run, data.TEST_SCENARIOS))
    summary = {p: {"passed": sum(r["results"][p]["pass"] for r in results), "total": len(results),
                   "avg_latency_ms": int(sum(r["results"][p]["latency_ms"] for r in results) / len(results))}
               for p in ai.PROVIDERS}
    return {"summary": summary, "results": results}


# ---- Serve the built React app (after `npm run build`) ----

DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        target = DIST / path
        if path and target.is_file():
            return FileResponse(target)
        # The page must not be cached, so a new build shows up on the next refresh
        # (the files in /assets have new names on every build, so they can be cached)
        return FileResponse(DIST / "index.html", headers={"Cache-Control": "no-cache"})
