"""Streamlit version of Rythu Mitra (Telangana x Bharat Vistaar prototype).

Run locally:   streamlit run streamlit_app.py
It reuses the same Python logic as the FastAPI backend (backend/app/*), so the
chatbot, login, Crop Doctor and pipeline behave exactly the same.
"""
import io
import os
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

# API keys: from backend/.env locally, or from Streamlit Cloud "Secrets". Must load before importing ai.
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "backend" / ".env")
try:
    for k in ("AI_MODE", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "CLAUDE_MODEL", "OPENAI_MODEL"):
        if k in st.secrets:
            os.environ[k] = str(st.secrets[k])
except Exception:  # no secrets file - fine, stays in mock mode
    pass

from app import ai, assistant, auth, data, diseases, pipeline  # noqa: E402

st.set_page_config(page_title="Rythu Mitra", page_icon="🌾", layout="wide")
st.markdown("""<style>
.block-container {padding-top: 2rem;}
.card {border: 1px solid rgba(128,128,128,.3); border-radius: 10px; padding: 12px 16px; margin-bottom: 10px;}
.big {font-size: 1.1rem; font-weight: 600;}
</style>""", unsafe_allow_html=True)

PROVIDER_LABEL = {"claude": "Claude", "gpt": "ChatGPT"}
ss = st.session_state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def current_user():
    """The logged-in user record, or None (also None after a server restart)."""
    return auth.user_for_token(ss.get("token"))


def log_query(intent, lang, provider, channel="Web chatbot", farmer_id=None):
    farmer = data.FARMER_INDEX.get((farmer_id or "").upper())
    data.QUERY_HISTORY.append({"date": date.today().isoformat(), "intent": intent, "lang": lang,
                               "channel": channel, "model": provider,
                               "district": farmer["district"] if farmer else "Unknown", "helpful": True})


def fmt(value, unit):
    """6400 g -> 6.4 kg, 1500 ml -> 1.5 L."""
    if unit == "g" and value >= 1000:
        return f"{value / 1000:g} kg"
    if unit == "ml" and value >= 1000:
        return f"{value / 1000:g} L"
    return f"{value:g} {unit}"


def model_picker(key):
    return st.radio("AI model", list(PROVIDER_LABEL), format_func=PROVIDER_LABEL.get, horizontal=True, key=key)


# ---------------------------------------------------------------------------
# Login, sign up, forgot / reset password
# ---------------------------------------------------------------------------

def auth_screen():
    st.title("🌾 Rythu Mitra")
    st.caption("Telangana State Intelligence Layer × Bharat Vistaar — prototype with dummy data")
    left, _ = st.columns([1, 1])
    with left:
        t_login, t_signup, t_forgot = st.tabs(["Log in", "Farmer sign-up", "Forgot password"])

        with t_login:
            with st.form("login"):
                uid = st.text_input("User ID")
                pwd = st.text_input("Password", type="password")
                if st.form_submit_button("Log in", type="primary", width="stretch"):
                    try:
                        ss.token, _ = auth.login(uid, pwd)
                        st.rerun()
                    except auth.AuthError as e:
                        st.error(str(e))
            st.caption("Demo user IDs and passwords are in the README (Demo accounts table).")

        with t_signup:
            st.write("Farmers: create an account with your Farmer ID and the mobile number on your department record.")
            with st.form("signup"):
                fid = st.text_input("Farmer ID", placeholder="e.g. TS1005")
                mob = st.text_input("Registered mobile number")
                p1 = st.text_input("New password", type="password", help="8+ characters with letters and numbers")
                p2 = st.text_input("Confirm password", type="password")
                if st.form_submit_button("Create account", width="stretch"):
                    try:
                        u = auth.register(fid, mob, p1, p2)
                        st.success(f"Account created for {u['name']}. You can log in now with user ID {u['user_id']}.")
                    except auth.AuthError as e:
                        st.error(str(e))

        with t_forgot:
            with st.form("forgot"):
                fuid = st.text_input("User ID", key="forgot_uid")
                if st.form_submit_button("Send reset code", width="stretch"):
                    try:
                        res = auth.forgot_password(fuid)
                        ss.reset_uid, ss.demo_otp, ss.sent_to = fuid, res["demo_otp"], res["sent_to"]
                    except auth.AuthError as e:
                        st.error(str(e))
            if ss.get("reset_uid"):
                st.info(f"A 6-digit code was sent to mobile {ss.sent_to}. It expires in {auth.OTP_MINUTES} minutes.\n\n"
                        f"**Demo only (no real SMS): your code is {ss.demo_otp}**")
                with st.form("reset"):
                    otp = st.text_input("Code")
                    r1 = st.text_input("New password", type="password")
                    r2 = st.text_input("Confirm new password", type="password")
                    if st.form_submit_button("Reset password", type="primary", width="stretch"):
                        try:
                            auth.reset_password(ss.reset_uid, otp, r1, r2)
                            ss.pop("reset_uid")
                            st.success("Password changed. Go to the Log in tab and sign in with your new password.")
                        except auth.AuthError as e:
                            st.error(str(e))


def sidebar(user):
    with st.sidebar:
        st.markdown(f"### 🌾 Rythu Mitra\n**{user['name']}**  \n{auth.ROLES[user['role']]}")
        staff = user["role"] != "farmer"
        pages = ["Farmer Chat", "Crop Doctor", "Farmer Services" if staff else "My Details"]
        if staff:
            pages += ["Claude vs ChatGPT", "Content Pipeline", "PMU Dashboard"]
        pages += ["How it works"]
        page = st.radio("Go to", pages, label_visibility="collapsed")
        st.divider()
        for p, s in ai.status().items():
            st.caption(f"{'🟢' if s['mode'] == 'live' else '🟡'} {s['model']}")
        with st.expander("Change password"):
            with st.form("change_pw", clear_on_submit=True):
                cur = st.text_input("Current password", type="password")
                n1 = st.text_input("New password", type="password")
                n2 = st.text_input("Confirm new password", type="password")
                if st.form_submit_button("Change"):
                    try:
                        auth.change_password(user, cur, n1, n2)
                        st.success("Password changed.")
                    except auth.AuthError as e:
                        st.error(str(e))
        if st.button("Log out", width="stretch"):
            auth.logout(ss.pop("token", None))
            ss.clear()
            st.rerun()
    return page


# ---------------------------------------------------------------------------
# Farmer Chat (Stages 1-4)
# ---------------------------------------------------------------------------

QUICK = {
    "en": ["What is the price of cotton today?", "Will it rain in Warangal this week?", "Tell me about Rythu Bharosa",
           "My maize has holes in the leaves, what should I spray?", "What is my application status?",
           "When does paddy procurement start?"],
    "te": ["మిరప ధర ఎంత?", "ఖమ్మం లో వాతావరణం ఎలా ఉంది?", "రైతు భరోసా పథకం గురించి చెప్పండి",
           "పత్తి పంటకు ఎరువు సలహా", "నా దరఖాస్తు స్థితి ఏమిటి?", "నా భూమి వివరాలు చూపించండి"],
}


def page_chat(user):
    st.header("💬 Farmer Chat")
    side, main = st.columns([1, 2.3])
    with side:
        provider = model_picker("chat_model")
        channel = st.radio("Channel", ["Web chatbot", "WhatsApp", "Voice bot"], horizontal=True)
        lang = st.radio("Example questions", ["te", "en"], format_func={"te": "తెలుగు", "en": "English"}.get, horizontal=True)
        if user["role"] == "farmer":
            farmer_id = user["farmer_id"]
            st.text_input("Logged in as", farmer_id, disabled=True)
        else:
            ids = [""] + [f["farmer_id"] for f in data.FARMERS]
            farmer_id = st.selectbox("Farmer ID (staff can test any farmer)", ids,
                                     format_func=lambda i: i and f"{i} · {data.FARMER_INDEX[i]['name']}" or "— none —")
        f = data.FARMER_INDEX.get(farmer_id or "")
        if f:
            st.success(f"✅ {f['name']} · {f['village']}, {f['district']} · {f['total_acres']} acres · {', '.join(f['crops'])}")
        st.write("**Try asking**")
        clicked = None
        for q in QUICK[lang]:
            if st.button(q, key=f"q_{q}", width="stretch"):
                clicked = q
        if st.button("🗑️ Clear chat"):
            ss.chat = []
            st.rerun()

    with main:
        ss.setdefault("chat", [])
        box = st.container(height=520)
        with box:
            with st.chat_message("assistant", avatar="🌾"):
                st.write("నమస్కారం! నేను రైతు మిత్ర 🌾  \nAsk me about mandi prices, weather, schemes or crop advice — "
                         "in Telugu or English. For a sick plant photo, use the **Crop Doctor** page.")
            for m in ss.chat:
                show_message(m)
        question = st.chat_input("మీ ప్రశ్న టైప్ చేయండి... / Type your question...") or clicked
        if question:
            ss.chat.append({"role": "user", "text": question})
            with box:
                show_message(ss.chat[-1])
                with st.spinner("Thinking..."):
                    gathered = assistant.gather(question, farmer_id or None)
                    res = ai.answer(provider, question, gathered)
            log_query(gathered["intent"], gathered["lang"], provider, channel, farmer_id)
            ss.chat.append({"role": "bot", **res, "stage": gathered["stage"], "sources": gathered["sources"]})
            st.rerun()


def show_message(m):
    if m["role"] == "user":
        with st.chat_message("user", avatar="👩‍🌾"):
            st.write(m["text"])
        return
    with st.chat_message("assistant", avatar="🌾"):
        st.markdown(m["text"].replace("\n", "  \n"))
        tags = [m["stage"], *m["sources"], f"{m['model']} · {m['latency_ms']} ms · {m['tokens_out']} tokens"]
        st.caption(" | ".join(tags))
        if m.get("note"):
            st.warning(m["note"])


# ---------------------------------------------------------------------------
# Crop Doctor
# ---------------------------------------------------------------------------

def page_doctor():
    st.header("🩺 Crop Doctor")
    st.write("Upload a photo of the affected plant. You get the problem, why it happens, and exactly how much to spray for your field.")
    c1, c2, c3, c4 = st.columns(4)
    lang = c1.radio("Language", ["en", "te"], format_func={"en": "English", "te": "తెలుగు"}.get, horizontal=True)
    crop = c2.selectbox("Crop (optional)", [""] + list(data.CROPS), format_func=lambda c: c or "Not sure")
    acres = c3.number_input("Field size (acres)", 0.1, 100.0, 1.0, 0.5)
    with c4:
        provider = model_picker("doctor_model")

    t_photo, t_lib = st.tabs(["📷 Diagnose a photo", "📚 Disease library"])
    with t_photo:
        up = st.file_uploader("Crop photo", type=["jpg", "jpeg", "png", "webp"])
        if up:
            st.image(up, width=320)
            if st.button("Analyse photo", type="primary"):
                with st.spinner("Looking at the leaves..."):
                    res = ai.diagnose(provider, up.getvalue(), up.type or "image/jpeg", lang, crop or None)
                log_query("pest_diagnosis", lang, provider)
                ss.diagnosis = (res, lang)
        if ss.get("diagnosis"):
            res, dlang = ss.diagnosis
            d = res["diagnosis"]
            if res["mode"] == "mock":
                st.info("Mock AI mode: the photo is not really analysed — a matching problem is picked from the library. "
                        "Add an API key to use real Claude / ChatGPT vision.")
            if d["status"] != "detected":
                st.warning(f"**{d['name']}** — {d['remedy']}")
            else:
                st.success(f"**{d['name']}** ({d['crop']}) — {round(d['confidence'] * 100)}% confidence")
                report(diseases.INDEX[d["disease_id"]], acres, lang)

    with t_lib:
        crops = sorted({d["crop"] for d in diseases.DISEASES})
        pick_crop = st.selectbox("Crop", crops, key="lib_crop")
        options = [d for d in diseases.DISEASES if d["crop"] == pick_crop]
        dz = st.selectbox("Problem", options, format_func=lambda d: f"{d['name']} ({d['type']})", key="lib_dz")
        report(dz, acres, lang)


def report(d, acres, lang):
    te = lang == "te"
    tank = diseases.SPRAYER_TANK_L
    st.subheader(f"{d['name_te'] if te else d['name']} · {data.CROPS[d['crop']] if te else d['crop']}")
    st.caption(d["type"])
    a, b = st.columns(2)
    a.markdown(f"**{'ఎందుకు వస్తుంది' if te else 'Why it happens'}**  \n{d['cause_te'] if te else d['cause']}")
    b.markdown(f"**{'లక్షణాలు' if te else 'Symptoms to check'}**  \n{d['symptoms_te'] if te else d['symptoms']}")

    st.markdown(f"#### {'మందుల ప్రణాళిక' if te else 'Treatment plan'} — {acres:g} {'ఎకరాలు' if te else 'acres'}")
    for t in diseases.plan_for(d, acres):
        icon = "🧪" if t["kind"] == "Chemical" else "🌿"
        with st.container(border=True):
            st.markdown(f"**{icon} {t['product']}** · {t['kind']}")
            if t["per"] == "litre":
                m = st.columns(5)
                m[0].metric("Per litre", fmt(t["dose"], t["unit"]))
                m[1].metric(f"Per {tank} L tank", fmt(t["per_tank"], t["unit"]))
                m[2].metric("Tanks needed", f"{t['tanks']:g}")
                m[3].metric("Total water", f"{t['water_total_l']:g} L")
                m[4].metric("Total to buy", fmt(t["total"], t["unit"]))
            else:
                m = st.columns(2)
                m[0].metric("Per acre", fmt(t["dose"], t["unit"]))
                m[1].metric("Total to buy", fmt(t["total"], t["unit"]))
            st.markdown(f"**Why:** {t['reason']}  \n**When:** {t['when']}  \n**Repeat:** {t['repeat']}  \n"
                        f"**How:** {t['method']}" + (f"  \n**Stop spraying {t['phi_days']} days before harvest.**" if t["phi_days"] else ""))
    a, b = st.columns(2)
    with a:
        st.markdown(f"**{'నివారణ' if te else 'Prevention'}**")
        for p in d["prevention_te" if te else "prevention"]:
            st.markdown(f"- {p}")
    with b:
        st.markdown(f"**{'భద్రత' if te else 'Spraying safety'}**")
        for p in diseases.SAFETY["te" if te else "en"]:
            st.markdown(f"- {p}")
    st.caption("Doses come only from the vetted library — the AI never writes doses. Demo values; confirm with your AEO before spraying.")


# ---------------------------------------------------------------------------
# Farmer Services / My Details (Stages 3-4)
# ---------------------------------------------------------------------------

def page_services(user):
    farmer_view = user["role"] == "farmer"
    st.header("👤 My Details" if farmer_view else "🗂️ Farmer Services")
    if farmer_view:
        fid = user["farmer_id"]
    else:
        fid = st.selectbox("Farmer", [f["farmer_id"] for f in data.FARMERS],
                           format_func=lambda i: f"{i} · {data.FARMER_INDEX[i]['name']} · {data.FARMER_INDEX[i]['district']}")
    f = data.FARMER_INDEX[fid]
    m = st.columns(4)
    m[0].metric("Farmer", f["name"])
    m[1].metric("District", f"{f['district']}")
    m[2].metric("Land", f"{f['total_acres']} acres")
    m[3].metric("Crops", ", ".join(f["crops"]))
    st.caption(f"Village {f['village']} · Bank {f['bank']} · Mobile {auth.mask(f['mobile'])}")

    t1, t2, t3, t4, t5 = st.tabs(["Applications & payments", "Land plots", "Grievances", "Weather", "Advisory"])
    with t1:
        apps = [assistant._app_view(a) for a in f["applications"]]
        st.dataframe(pd.DataFrame(apps)[["app_id", "scheme", "applied_on", "status", "amount", "credited_on"]],
                     hide_index=True, width="stretch")
    with t2:
        st.dataframe(pd.DataFrame(f["plots"]), hide_index=True, width="stretch")
    with t3:
        mine = [g for g in data.GRIEVANCES if g["farmer_id"] == fid]
        if mine:
            st.dataframe(pd.DataFrame(mine)[["grievance_id", "category", "description", "status", "created_on", "channel"]],
                         hide_index=True, width="stretch")
        else:
            st.write("No grievances yet.")
        with st.form("griev", clear_on_submit=True):
            st.write("**Raise a new grievance**")
            cat = st.selectbox("Category", data.GRIEVANCE_CATEGORIES)
            desc = st.text_area("Describe the problem")
            if st.form_submit_button("Submit grievance"):
                if not desc.strip():
                    st.error("Please describe the problem.")
                else:
                    g = {"grievance_id": f"GRV-{2401 + len(data.GRIEVANCES)}", "farmer_id": fid, "farmer_name": f["name"],
                         "district": f["district"], "category": cat, "description": desc.strip(), "status": "Open",
                         "created_on": date.today().isoformat(), "channel": "Web chatbot"}
                    data.GRIEVANCES.append(g)
                    st.success(f"Grievance {g['grievance_id']} registered.")
                    st.rerun()
    with t4:
        w = pd.DataFrame(data.WEATHER[f["district"]])[["date", "condition", "max_c", "min_c", "rain_mm", "humidity"]]
        st.dataframe(w, hide_index=True, width="stretch")
    with t5:
        for c in f["crops"]:
            st.markdown(f"**{c}**")
            for tip in data.ADVISORIES[c]["en"]:
                st.markdown(f"- {tip}")

    if not farmer_view:
        st.divider()
        st.subheader("All grievances")
        rows = sorted(data.GRIEVANCES, key=lambda g: g["created_on"], reverse=True)
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


# ---------------------------------------------------------------------------
# Claude vs ChatGPT (testing, proposal 2.9)
# ---------------------------------------------------------------------------

def page_compare():
    st.header("⚖️ Claude vs ChatGPT")
    q = st.text_input("Question", "రైతు భరోసా పథకం గురించి చెప్పండి")
    if st.button("Compare", type="primary") and q.strip():
        gathered = assistant.gather(q)
        with ThreadPoolExecutor() as pool:
            results = dict(zip(PROVIDER_LABEL, pool.map(lambda p: ai.answer(p, q, gathered), PROVIDER_LABEL)))
        st.caption(f"Intent: {gathered['intent']} · {gathered['stage']} · Sources: {', '.join(gathered['sources']) or '—'}")
        cols = st.columns(2)
        for col, (p, r) in zip(cols, results.items()):
            with col, st.container(border=True):
                st.markdown(f"**{r['model']}** — {r['latency_ms']} ms · {r['tokens_out']} tokens")
                st.markdown(r["text"].replace("\n", "  \n"))

    st.divider()
    st.subheader("Agreed test scenarios")
    if st.button("Run all tests"):
        with st.spinner("Running scenarios on both models..."):
            ss.eval = run_evaluation()
    if ss.get("eval"):
        summary, rows = ss.eval
        cols = st.columns(2)
        for col, p in zip(cols, PROVIDER_LABEL):
            s = summary[p]
            col.metric(PROVIDER_LABEL[p], f"{s['passed']}/{s['total']} passed", f"avg {s['avg_latency_ms']} ms", delta_color="off")
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def run_evaluation():
    def run(sc):
        gathered = assistant.gather(sc["question"])
        row = {"id": sc["id"], "question": sc["question"], "intent": gathered["intent"]}
        for p in PROVIDER_LABEL:
            r = ai.answer(p, sc["question"], gathered)
            text = r["text"].lower()
            hits = [k for k in sc["expect"] if k.lower() in text]
            lang_ok = assistant.detect_lang(r["text"]) == sc["lang"] or sc["lang"] == "en"
            row[PROVIDER_LABEL[p]] = "✅ pass" if len(hits) == len(sc["expect"]) and lang_ok else "❌ fail"
            row[f"{PROVIDER_LABEL[p]} ms"] = r["latency_ms"]
        return row

    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(run, data.TEST_SCENARIOS))
    summary = {p: {"passed": sum(r[PROVIDER_LABEL[p]].startswith("✅") for r in rows), "total": len(rows),
                   "avg_latency_ms": int(sum(r[f"{PROVIDER_LABEL[p]} ms"] for r in rows) / len(rows))}
               for p in PROVIDER_LABEL}
    return summary, rows


# ---------------------------------------------------------------------------
# Content Pipeline (Stage 2)
# ---------------------------------------------------------------------------

def page_pipeline(user):
    st.header("📄 Content Pipeline")
    st.write("Documents move through 11 stages. Only **Completed** documents can be used by the chatbot.")
    role = user["role"]
    if role == "admin":
        role = st.selectbox("Acting as", list(auth.ROLES), format_func=auth.ROLES.get)

    if user["role"] in ("contributor", "admin"):
        with st.expander("➕ Upload a new document"):
            with st.form("upload", clear_on_submit=True):
                title = st.text_input("Title")
                c1, c2 = st.columns(2)
                category = c1.selectbox("Category", ["Circular", "Scheme guideline", "Advisory", "Notification"])
                lang = c2.selectbox("Language", ["te", "en"], format_func={"te": "Telugu", "en": "English"}.get)
                text = st.text_area("Paste the text")
                file = st.file_uploader("…or upload a .txt / .pdf", type=["txt", "pdf"])
                if st.form_submit_button("Upload"):
                    body = text.strip()
                    if file is not None:
                        raw = file.getvalue()
                        if file.name.lower().endswith(".pdf"):
                            from pypdf import PdfReader
                            body = "\n\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(raw)).pages).strip()
                        else:
                            body = raw.decode("utf-8", errors="ignore").strip()
                    if not title.strip() or not body:
                        st.error("Add a title and the document text (or a file).")
                    else:
                        pipeline.add_document(title.strip(), body, lang=lang, category=category, uploaded_by=user["name"])
                        st.success("Uploaded.")
                        st.rerun()

    for doc in reversed(pipeline.DOCUMENTS):
        d = pipeline.public(doc)
        done = d["stage"] == pipeline.LAST
        with st.expander(f"{'✅' if done else '⏳'} {d['title']} — {d['stage_label']}"):
            st.progress(d["stage"] / pipeline.LAST, text=f"Stage {d['stage'] + 1} of {pipeline.LAST + 1}: {d['stage_label']}")
            if not done:
                actor = d["next_actor"]
                allowed = role == "admin" or actor == "system" or actor == role
                who = "Bharat Vistaar platform (automatic)" if actor == "system" else auth.ROLES[actor]
                st.write(f"Next step: **{d['next_label']}** — done by {who}")
                if st.button(f"Do next step: {d['next_label']}", key=f"adv_{d['id']}", disabled=not allowed, type="primary"):
                    by = "Bharat Vistaar platform" if actor == "system" else f"{user['name']} ({auth.ROLES[role]})"
                    pipeline.advance(doc, by=by, translate_fn=ai.translate)
                    st.rerun()
                if not allowed:
                    st.caption(f"Only a {who} can do this step.")
            a, b = st.columns(2)
            a.text_area("Original text", d["raw_text"], height=150, disabled=True, key=f"raw_{d['id']}")
            b.text_area("English translation", d.get("translation") or "—", height=150, disabled=True, key=f"tr_{d['id']}")
            st.dataframe(pd.DataFrame(d["history"]), hide_index=True, width="stretch")


# ---------------------------------------------------------------------------
# PMU Dashboard
# ---------------------------------------------------------------------------

def page_dashboard():
    st.header("📊 PMU Dashboard")
    rows = data.QUERY_HISTORY
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    docs = pipeline.DOCUMENTS
    m = st.columns(4)
    m[0].metric("Total queries", len(rows), f"{sum(r['date'] >= week_ago for r in rows)} in last 7 days")
    m[1].metric("Telugu share", f"{round(100 * sum(r['lang'] == 'te' for r in rows) / max(1, len(rows)))}%")
    m[2].metric("Docs published", f"{sum(d['stage'] == pipeline.LAST for d in docs)} / {len(docs)}")
    m[3].metric("Open grievances", sum(g["status"] != "Resolved" for g in data.GRIEVANCES))

    by_day = Counter(r["date"] for r in rows)
    st.subheader("Queries per day")
    st.line_chart(pd.DataFrame({"queries": [by_day[d] for d in sorted(by_day)]}, index=sorted(by_day)).tail(30))
    a, b, c = st.columns(3)
    for col, key, title in ((a, "intent", "By topic"), (b, "channel", "By channel"), (c, "district", "By district")):
        counts = Counter(r[key] for r in rows if r[key] != "Unknown").most_common(12)
        col.markdown(f"**{title}**")
        col.bar_chart(pd.DataFrame(counts, columns=[key, "queries"]).set_index(key), horizontal=True)

    st.subheader("Integration tracker")
    st.dataframe(pd.DataFrame(data.TRACKER), hide_index=True, width="stretch")
    st.subheader("Risks & issues register")
    st.dataframe(pd.DataFrame(data.ISSUES), hide_index=True, width="stretch")


# ---------------------------------------------------------------------------
# How it works
# ---------------------------------------------------------------------------

def page_about():
    st.header("ℹ️ How it works")
    st.markdown("""
**Rythu Mitra** is a prototype of the Telangana State Intelligence Layer integrated with Bharat Vistaar.
All data is **dummy data** for demonstration.

**Mock AI mode (default, no API keys).** Understanding the question (topic, Telugu/English, crop, district) and
looking up facts (prices, weather, schemes, farmer records, State circulars) are real. Only the final wording is
written from templates — Claude-mock uses a warm bullet style, ChatGPT-mock a short numbered style. Latency and
token counts are simulated. Photo diagnosis picks a matching problem from the library instead of looking at the photo.

**Live mode.** Add `ANTHROPIC_API_KEY` and/or `OPENAI_API_KEY` (in `backend/.env` locally, or in Streamlit Cloud →
Settings → Secrets). The real models then write the replies from the same facts and look at crop photos.

**Safety.** In Crop Doctor the AI only identifies the problem. Doses always come from the vetted table.

| Page | Proposal |
|---|---|
| Login | §2.8 Admin / Contributor / Reviewer roles |
| Farmer Chat | Stage 1 chatbot & voice bot, §2.6 channels |
| Crop Doctor | §2.7 image-based crop/pest diagnosis |
| Claude vs ChatGPT | §2.9 testing against agreed scenarios |
| Content Pipeline | Stage 2, §2.4 ingestion pipeline |
| Farmer Services | Stages 3 & 4 — applications, payments, grievances, land |
| PMU Dashboard | §2.9 governance & reporting, §2.10 PMU |
""")


# ---------------------------------------------------------------------------

user = current_user()
if not user:
    ss.pop("token", None)
    auth_screen()
else:
    page = sidebar(user)
    staff = user["role"] != "farmer"
    if page == "Farmer Chat":
        page_chat(user)
    elif page == "Crop Doctor":
        page_doctor()
    elif page in ("Farmer Services", "My Details"):
        page_services(user)
    elif page == "Claude vs ChatGPT" and staff:
        page_compare()
    elif page == "Content Pipeline" and staff:
        page_pipeline(user)
    elif page == "PMU Dashboard" and staff:
        page_dashboard()
    else:
        page_about()
