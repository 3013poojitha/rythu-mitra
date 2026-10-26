"""Streamlit version of Rythu Mitra (Telangana x Bharat Vistaar prototype).

Run locally:   streamlit run streamlit_app.py
It reuses the same Python logic as the FastAPI backend (backend/app/*), so the
chatbot, login, Crop Doctor and pipeline behave exactly the same. The look
matches the React app: colours in .streamlit/config.toml, layout in CSS below.
"""
import html
import io
import os
import re
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

st.set_page_config(page_title="Rythu Mitra - Telangana x Bharat Vistaar", page_icon="🌾", layout="wide")

PROVIDER_LABEL = {"claude": "Claude", "gpt": "ChatGPT"}
ss = st.session_state

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+Telugu:wght@400;600&display=swap');
:root { --bg:#f4f7f2; --ink:#1d2a1f; --muted:#66756a; --line:#e1e8df; --brand:#1f7a3e; --brand-dark:#145c2c;
        --brand-soft:#e6f3ea; --accent:#e8a317; --amber:#b7791f; --claude:#c96442; --gpt:#10a37f;
        --shadow:0 1px 2px rgba(20,40,25,.06),0 4px 16px rgba(20,40,25,.05); }
html, body, .stApp, .stApp button, .stApp input, .stApp textarea, .stApp p, .stApp li, .stApp label {
  font-family: Inter, "Noto Sans Telugu", system-ui, sans-serif; }
.stApp p, .stApp li { font-size: 14px; }

/* Remove Streamlit chrome so the page looks like the web app */
header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"], footer, #MainMenu, [data-testid="stDecoration"] { display: none !important; }
[data-testid="stMainBlockContainer"], .block-container { padding: 0 0 40px !important; max-width: none !important; }
[data-testid="stAppViewContainer"] > .stMain { padding-top: 0; }

/* Top bar */
.st-key-topbar { background: linear-gradient(90deg, #145c2c, #1f7a3e); color: #fff; padding: 12px 24px; }
.brand { display: flex; gap: 12px; align-items: center; }
.logo { font-size: 30px; background: rgba(255,255,255,.15); border-radius: 10px; padding: 2px 8px; line-height: 1.3; }
.brand-title { font-size: 19px; font-weight: 700; color: #fff; }
.te { font-family: "Noto Sans Telugu", sans-serif; font-weight: 600; color: var(--accent); margin-left: 6px; }
.brand-title .te { color: #ffd77a; }
.brand-sub { font-size: 12px; opacity: .85; color: #fff; }
.status { display: flex; gap: 6px; justify-content: flex-end; flex-wrap: wrap; }
.pill { display: inline-block; padding: 2px 9px; border-radius: 99px; font-size: 12px; font-weight: 600; white-space: nowrap; }
.pill.amber { background: #ffd77a; color: #4d3800; }
.pill.green { background: #c9f2d5; color: #0d4d22; }
.pill.grey { background: #eceeed; color: #5b625d; }
.pill.soft { background: var(--brand-soft); color: var(--brand-dark); }
.st-key-topbar [data-testid="stPopover"] button { background: rgba(255,255,255,.12); border-color: rgba(255,255,255,.25); color: #fff; }
.st-key-topbar [data-testid="stPopover"] button p { color: #fff; font-weight: 600; }

/* Tab bar */
.st-key-nav { background: #fff; border-bottom: 1px solid var(--line); padding: 0 24px; margin-top: -1rem; }
.st-key-nav [role="radiogroup"] { gap: 4px; flex-wrap: nowrap; overflow-x: auto; }
.st-key-nav [data-testid="stRadioOption"] { padding: 10px 14px !important; margin: 0 !important; border-bottom: 3px solid transparent !important; white-space: nowrap; }
.st-key-nav [data-testid="stRadioOption"] > div > div:first-child { display: none; }
.st-key-nav [data-testid="stRadioOption"] p { font-weight: 600; font-size: 14px; }
.st-key-nav [data-testid="stRadioOption"][data-selected="true"] { border-bottom-color: var(--brand) !important; }
.st-key-nav [data-testid="stRadioOption"][data-selected="true"] p { color: var(--brand); }
/* Hide the empty blocks that only carry this stylesheet, so the top bar touches the top */
.stElementContainer:has(style) { display: none; }
/* Selected segment = solid green, like the React .seg control */
button[data-variant="segmented_control"][aria-checked="true"] { background: var(--brand) !important; border-color: var(--brand) !important; }
button[data-variant="segmented_control"][aria-checked="true"] p, button[data-variant="segmented_control"][aria-checked="true"] div { color: #fff !important; font-weight: 600; }
.banner { background: #fff7e3; border-bottom: 1px solid #f3e1b0; padding: 8px 24px; font-size: 13px; margin-top: -1rem; }

/* Page content */
.st-key-content { padding: 20px 24px 0; max-width: 1400px; margin: 0 auto; }
.st-key-content h2 { font-size: 18px; margin: 0; padding: 0; }
.st-key-content h3 { font-size: 15px; margin: 0; padding: 0 0 4px; }
[class*="st-key-panel"] { background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 16px; box-shadow: var(--shadow); }
.muted { color: var(--muted); font-size: 13px; }
.tag { display: inline-block; font-size: 11px; padding: 2px 7px; border-radius: 6px; background: #f0f3ef; color: var(--muted); margin: 2px 2px 0 0; }
.tag.stage { background: var(--brand-soft); color: var(--brand-dark); font-weight: 600; }
.tag.model { background: #f3eefc; color: #5b3fa3; }
.farmer-chip { background: var(--brand-soft); border-radius: 8px; padding: 8px 10px; font-weight: 600; font-size: 14px; }
.farmer-chip small { font-weight: 400; color: var(--muted); }
.st-key-quick button { justify-content: flex-start; text-align: left; background: #fafcf9; min-height: 0; padding: 6px 10px; }
.st-key-quick button p { font-size: 13px; text-align: left; }
.st-key-quick button > div { justify-content: flex-start; width: 100%; }
.st-key-quick button:hover { border-color: var(--brand); color: var(--ink); }
[data-testid="stWidgetLabel"] p { font-size: 12px !important; font-weight: 600; color: var(--muted); }

/* Phone-style chat */
.st-key-phone, .st-key-phone_wa { background: #fff; border: 1px solid var(--line); border-radius: 18px; overflow: hidden; box-shadow: var(--shadow); gap: 0; }
.phone-head { display: flex; gap: 10px; align-items: center; padding: 12px 16px; background: var(--brand); color: #fff; }
.st-key-phone_wa .phone-head { background: #075e54; }
.phone-head b { color: #fff; } .phone-head small { display: block; opacity: .85; font-size: 12px; color: #fff; }
.avatar { width: 38px; height: 38px; display: grid; place-items: center; border-radius: 50%; background: rgba(255,255,255,.2); font-size: 20px; }
.st-key-msgs { background: #f7faf6; padding: 16px; border-radius: 0; border: 0; }
.st-key-phone_wa .st-key-msgs { background: #ece5dd; }
.msg { width: fit-content; max-width: 78%; padding: 10px 13px; border-radius: 14px; box-shadow: 0 1px 1px rgba(0,0,0,.05); font-size: 14px; line-height: 1.5; }
.msg.user { margin-left: auto; background: var(--brand); color: #fff; border-bottom-right-radius: 4px; }
.st-key-phone_wa .msg.user { background: #dcf8c6; color: var(--ink); }
.msg.bot { background: #fff; border: 1px solid var(--line); border-bottom-left-radius: 4px; }
.msg .meta { margin-top: 8px; }
.msg .note { margin-top: 6px; font-size: 12px; color: var(--amber); }
.st-key-phone [data-testid="stChatInput"], .st-key-phone_wa [data-testid="stChatInput"] { padding: 10px; border-top: 1px solid var(--line); }

/* Metric tiles (KPIs) */
[data-testid="stMetric"] { background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 14px; box-shadow: var(--shadow); }
[data-testid="stMetricValue"] { color: var(--brand-dark); font-size: 24px; font-weight: 700; }
[data-testid="stMetricLabel"] p { color: var(--muted); font-size: 12px; }

/* Crop Doctor */
.dz-head { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; align-items: center; }
.dz-name { font-size: 18px; font-weight: 700; }
.grid2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin: 12px 0; }
.box { background: #fafcf9; border: 1px solid var(--line); border-radius: 10px; padding: 12px; font-size: 14px; }
.box b { display: block; margin-bottom: 4px; }
.treat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin: 8px 0; }
.treat { border: 1px solid var(--line); border-radius: 10px; padding: 12px; font-size: 13px; background: #fff; }
.treat.best { border: 2px solid var(--brand); }
.treat .t-name { font-weight: 700; font-size: 14px; }
.qty { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; margin: 8px 0; }
.qty div { background: var(--brand-soft); border-radius: 8px; padding: 6px 8px; }
.qty small { display: block; color: var(--muted); font-size: 11px; }
.qty b { color: var(--brand-dark); font-size: 15px; }
.qty .total { background: #fff7e3; } .qty .total b { color: #8a5a00; }
.phi { color: #c53b32; font-weight: 600; }
.demo-otp { background: #fff7e3; border: 1px dashed var(--accent); border-radius: 8px; padding: 10px; margin: 10px 0; font-size: 13px; }
.demo-otp b { font-size: 18px; letter-spacing: 3px; }

/* Model comparison cards */
.st-key-panel_claude { border-top: 4px solid var(--claude); }
.st-key-panel_gpt { border-top: 4px solid var(--gpt); }

@media (max-width: 820px) {
  .st-key-topbar, .st-key-nav, .banner { padding-left: 16px; padding-right: 16px; }
  .st-key-content { padding: 16px 16px 0; }
  .grid2 { grid-template-columns: 1fr; }
  .msg { max-width: 92%; }
}
</style>
"""

AUTH_CSS = """
<style>
.stApp { background: linear-gradient(135deg, #145c2c 0%, #1f7a3e 55%, #f4f7f2 55%) !important; }
[data-testid="stMainBlockContainer"], .block-container { padding: 40px clamp(16px, 6vw, 100px) !important; }
.auth-hero { color: #fff; padding-top: 40px; }
.auth-hero h1 { font-size: 34px; margin: 12px 0 4px; color: #fff; padding: 0; }
.auth-hero h1 .te { color: #ffd77a; }
.auth-hero p, .auth-hero li { color: #fff; font-size: 15px; }
.auth-hero ul { padding-left: 20px; line-height: 2; }
.auth-hero small { opacity: .8; }
.logo.big { font-size: 44px; display: inline-block; padding: 6px 14px; }
.st-key-panel_auth { padding: 28px; }
@media (max-width: 820px) {
  .stApp { background: linear-gradient(180deg, #145c2c 0%, #1f7a3e 300px, #f4f7f2 300px) !important; }
  .auth-hero ul { display: none; }
  .auth-hero { padding-top: 0; }
}
</style>
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def H(markup):
    st.markdown(markup, unsafe_allow_html=True)


def rich(text):
    """Safe HTML for a chat reply: escape, then **bold** and line breaks."""
    t = html.escape(text or "")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return t.replace("\n", "<br>")


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


def seg(label, options, key, labels=None, default=None):
    """Segmented buttons like the React app's .seg control; never returns None."""
    val = st.segmented_control(label, options, key=key, default=default or options[0],
                               format_func=(labels or {}).get if labels else str)
    return val or default or options[0]


# ---------------------------------------------------------------------------
# Login, sign up, forgot / reset password
# ---------------------------------------------------------------------------

def auth_screen():
    H(AUTH_CSS)
    hero, card = st.columns([1.2, 1], gap="large")
    with hero:
        H("""<div class="auth-hero"><div class="logo big">🌾</div>
<h1>Rythu Mitra <span class="te">రైతు మిత్ర</span></h1>
<p>Telangana Agriculture Department × Bharat Vistaar</p>
<ul><li>Telugu &amp; English farmer assistant</li><li>Crop disease detection with spray guidance</li>
<li>Scheme, payment and grievance status</li><li>Content pipeline and PMU dashboard for staff</li></ul>
<small>Prototype with dummy data</small></div>""")
    with card, st.container(key="panel_auth"):
        if ss.get("notice"):
            st.success(ss.pop("notice"))
        mode = ss.get("auth_mode", "login")
        if mode == "login":
            login_form()
        elif mode == "register":
            register_form()
        else:
            forgot_form()


def go(mode):
    ss.auth_mode = mode


def login_form():
    st.markdown("### Log in")
    H('<p class="muted">Farmers use their Farmer ID (e.g. TS1002). Staff use their department user ID.</p>')
    with st.form("login", border=False):
        uid = st.text_input("User ID")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Log in", type="primary", width="stretch"):
            try:
                ss.token, _ = auth.login(uid, pwd)
                st.rerun()
            except auth.AuthError as e:
                st.error(str(e))
    a, b = st.columns(2)
    a.button("Forgot password?", on_click=go, args=("forgot",), type="tertiary")
    b.button("New farmer? Create account", on_click=go, args=("register",), type="tertiary")
    H('<p class="muted">Demo user IDs and passwords are in the README (Demo accounts table).</p>')


def register_form():
    st.markdown("### Farmer sign-up")
    H('<p class="muted">Use your Farmer ID and the mobile number on your department record.</p>')
    with st.form("signup", border=False):
        fid = st.text_input("Farmer ID", placeholder="e.g. TS1005")
        mob = st.text_input("Registered mobile number")
        p1 = st.text_input("New password", type="password", help="8+ characters with letters and numbers")
        p2 = st.text_input("Confirm password", type="password")
        if st.form_submit_button("Create account", type="primary", width="stretch"):
            try:
                u = auth.register(fid, mob, p1, p2)
                ss.notice = f"Account created for {u['name']}. Log in with user ID {u['user_id']}."
                go("login")
                st.rerun()
            except auth.AuthError as e:
                st.error(str(e))
    st.button("← Back to log in", on_click=go, args=("login",), type="tertiary")


def forgot_form():
    if not ss.get("reset_uid"):
        st.markdown("### Forgot password")
        H('<p class="muted">Enter your user ID. We will send a 6-digit code to your registered mobile.</p>')
        with st.form("forgot", border=False):
            fuid = st.text_input("User ID")
            if st.form_submit_button("Send code", type="primary", width="stretch"):
                try:
                    res = auth.forgot_password(fuid)
                    ss.reset_uid, ss.demo_otp, ss.sent_to = fuid, res["demo_otp"], res["sent_to"]
                    st.rerun()
                except auth.AuthError as e:
                    st.error(str(e))
    else:
        st.markdown("### Reset password")
        H(f'<p class="muted">Code sent to mobile {ss.sent_to}. It expires in {auth.OTP_MINUTES} minutes.</p>'
          f'<div class="demo-otp">Demo only — no real SMS is sent. Your code is <b>{ss.demo_otp}</b></div>')
        with st.form("reset", border=False):
            otp = st.text_input("6-digit code")
            r1 = st.text_input("New password", type="password", help="8+ characters with letters and numbers")
            r2 = st.text_input("Confirm new password", type="password")
            if st.form_submit_button("Reset password", type="primary", width="stretch"):
                try:
                    auth.reset_password(ss.reset_uid, otp, r1, r2)
                    ss.pop("reset_uid")
                    ss.notice = "Password changed. Log in with your new password."
                    go("login")
                    st.rerun()
                except auth.AuthError as e:
                    st.error(str(e))
    st.button("← Back to log in", on_click=lambda: (ss.pop("reset_uid", None), go("login")), type="tertiary")


# ---------------------------------------------------------------------------
# Top bar and tabs (same as the React header)
# ---------------------------------------------------------------------------

TABS = [("Farmer Chat", None),("Crop Doctor", None), ("Farmer Services", "My Details"),
        ("Claude vs ChatGPT", None), ("Content Pipeline", None), ("PMU Dashboard", None), ("How it works", None)]
STAFF_TABS = {"Claude vs ChatGPT", "Content Pipeline", "PMU Dashboard"}


def header(user):
    status = ai.status()
    with st.container(key="topbar"):
        left, right = st.columns([3, 2], vertical_alignment="center")
        left.markdown("""<div class="brand"><div class="logo">🌾</div><div>
<div class="brand-title">Rythu Mitra <span class="te">రైతు మిత్ర</span></div>
<div class="brand-sub">Telangana Agriculture Dept × Bharat Vistaar · Prototype with dummy data</div></div></div>""",
                      unsafe_allow_html=True)
        with right:
            pills, menu = st.columns([3, 2], vertical_alignment="center")
            pills.markdown('<div class="status">' + "".join(
                f'<span class="pill {"green" if p["mode"] == "live" else "amber"}">{p["label"]}: '
                f'{"Live" if p["mode"] == "live" else "Mock AI"}</span>' for p in status.values()) + "</div>",
                unsafe_allow_html=True)
            with menu.popover(f"👤 {user['name']}", width="stretch"):
                st.markdown(f"**{user['user_id']}**  \n{auth.ROLES[user['role']]} · Mobile {auth.mask(user['mobile'])}")
                with st.form("change_pw", clear_on_submit=True):
                    st.markdown("**🔑 Change password**")
                    cur = st.text_input("Current password", type="password")
                    n1 = st.text_input("New password", type="password")
                    n2 = st.text_input("Confirm new password", type="password")
                    if st.form_submit_button("Change password"):
                        try:
                            auth.change_password(user, cur, n1, n2)
                            st.success("Password changed.")
                        except auth.AuthError as e:
                            st.error(str(e))
                if st.button("🚪 Log out", width="stretch"):
                    auth.logout(ss.pop("token", None))
                    ss.clear()
                    st.rerun()

    staff = user["role"] != "farmer"
    names = [t for t, _ in TABS if staff or t not in STAFF_TABS]
    labels = {t: (fl if not staff and fl and t == "Farmer Services" else t) for t, fl in TABS}
    with st.container(key="nav"):
        page = st.radio("Page", names, horizontal=True, label_visibility="collapsed", format_func=labels.get, key="page")
    if any(p["mode"] == "mock" for p in status.values()) and page != "How it works":
        H('<div class="banner">Running in <b>Mock AI mode</b> — no API keys needed. Answers come from dummy data '
          'with simulated model replies. See <b>How it works</b>.</div>')
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
WELCOME = ("నమస్కారం! నేను రైతు మిత్ర 🌾\nNamaskaram! Ask me about mandi prices, weather, schemes, crop advice — "
           "in Telugu or English. For a photo of a sick plant, use **Crop Doctor**.")


def page_chat(user):
    side, main = st.columns([1, 2.6], gap="medium")
    with side, st.container(key="panel_settings"):
        st.markdown("### Settings")
        provider = seg("AI model", list(PROVIDER_LABEL), "chat_model", PROVIDER_LABEL)
        channel = seg("Channel", ["Web chatbot", "WhatsApp", "Voice bot"], "channel",
                      {"Web chatbot": "Web", "WhatsApp": "WhatsApp", "Voice bot": "Voice"})
        lang = seg("Language", ["te", "en"], "lang", {"te": "తెలుగు", "en": "English"})
        if user["role"] == "farmer":
            farmer_id = user["farmer_id"]
            st.text_input("Logged in as", farmer_id, disabled=True)
        else:
            ids = [""] + [f["farmer_id"] for f in data.FARMERS]
            farmer_id = st.selectbox("Farmer ID (staff can test any farmer)", ids,
                                     format_func=lambda i: i and f"{i} · {data.FARMER_INDEX[i]['name']}" or "— optional —")
        f = data.FARMER_INDEX.get(farmer_id or "")
        if f:
            H(f'<div class="farmer-chip">✅ {f["name"]}<br><small>{f["village"]}, {f["district"]} · '
              f'{f["total_acres"]} acres · {", ".join(f["crops"])}</small></div>')
        st.markdown("**Try asking**")
        clicked = None
        with st.container(key="quick", gap="small"):
            for q in QUICK[lang]:
                if st.button(q, key=f"q_{q}", width="stretch"):
                    clicked = q
        if st.button("🗑️ Clear chat", type="tertiary"):
            ss.chat = []
            st.rerun()

    with main, st.container(key="phone_wa" if channel == "WhatsApp" else "phone"):
        sub = {"WhatsApp": "Telangana Agriculture Dept · Verified business",
               "Voice bot": "Voice bot · replies can be read aloud"}.get(channel, "agri.telangana.gov.in · Chat")
        H(f'<div class="phone-head"><div class="avatar">🌾</div><div><b>Rythu Mitra</b><small>{sub}</small></div></div>')
        ss.setdefault("chat", [])
        box = st.container(height=480, key="msgs", border=False)
        with box:
            H(f'<div class="msg bot">{rich(WELCOME)}</div>')
            for m in ss.chat:
                show_message(m)
        question = st.chat_input("మీ ప్రశ్న టైప్ చేయండి..." if lang == "te" else "Type your question...") or clicked
        if question:
            ss.chat.append({"role": "user", "text": question})
            with box:
                show_message(ss.chat[-1])
                with st.spinner("Typing..."):
                    gathered = assistant.gather(question, farmer_id or None)
                    res = ai.answer(provider, question, gathered)
            log_query(gathered["intent"], gathered["lang"], provider, channel, farmer_id)
            ss.chat.append({"role": "bot", **res, "stage": gathered["stage"], "sources": gathered["sources"]})
            st.rerun()


def show_message(m):
    if m["role"] == "user":
        H(f'<div class="msg user">{rich(m["text"])}</div>')
        return
    tags = (f'<span class="tag stage">{html.escape(m["stage"])}</span>'
            + "".join(f'<span class="tag">{html.escape(s)}</span>' for s in m["sources"])
            + f'<span class="tag model">{m["model"]} · {m["latency_ms"]} ms · {m["tokens_out"]} tokens</span>')
    note = f'<div class="note">{html.escape(m["note"])}</div>' if m.get("note") else ""
    H(f'<div class="msg bot">{rich(m["text"])}<div class="meta">{tags}</div>{note}</div>')


# ---------------------------------------------------------------------------
# Crop Doctor
# ---------------------------------------------------------------------------

def page_doctor():
    top_l, top_r = st.columns([1.3, 1], gap="medium")
    with top_r, st.container(key="panel_doc_settings"):
        st.markdown("### Your field")
        lang = seg("Language", ["en", "te"], "doc_lang", {"en": "English", "te": "తెలుగు"})
        crop = st.selectbox("Crop (optional)", [""] + list(data.CROPS), format_func=lambda c: c or "Not sure")
        acres = st.number_input("Field size (acres)", 0.1, 100.0, 1.0, 0.5)
        provider = seg("AI model", list(PROVIDER_LABEL), "doctor_model", PROVIDER_LABEL)
    with top_l, st.container(key="panel_photo"):
        st.markdown("## 🩺 Crop Doctor")
        H('<p class="muted">Upload a photo of the affected plant. You get the problem, why it happens, and exactly '
          'how much to spray for your field.</p>')
        up = st.file_uploader("Crop photo", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
        if up:
            c1, c2 = st.columns([1, 1.4], vertical_alignment="center")
            c1.image(up, width="stretch")
            if c2.button("🔍 Analyse photo", type="primary", width="stretch"):
                with st.spinner("Looking at the leaves..."):
                    res = ai.diagnose(provider, up.getvalue(), up.type or "image/jpeg", lang, crop or None)
                log_query("pest_diagnosis", lang, provider)
                ss.diagnosis = res

    res = ss.get("diagnosis")
    if res:
        d = res["diagnosis"]
        with st.container(key="panel_result"):
            if res["mode"] == "mock":
                H('<div class="demo-otp">Mock AI mode: the photo is not really analysed — a matching problem is picked '
                  'from the library. Add an API key to use real Claude / ChatGPT vision.</div>')
            if d["status"] != "detected":
                st.warning(f"**{d['name']}** — {d['remedy']}")
            else:
                report(diseases.INDEX[d["disease_id"]], acres, lang, confidence=d["confidence"])

    with st.container(key="panel_library"):
        st.markdown("### 📚 Disease library")
        crops = sorted({d["crop"] for d in diseases.DISEASES})
        pick_crop = st.pills("Crop", crops, default=crops[0], key="lib_crop") or crops[0]
        options = [d for d in diseases.DISEASES if d["crop"] == pick_crop]
        dz = st.selectbox("Problem", options, format_func=lambda d: f"{d['name']} ({d['type']})", key="lib_dz")
        report(dz, acres, lang)


def report(d, acres, lang, confidence=None):
    te = lang == "te"
    tank = diseases.SPRAYER_TANK_L
    conf = f'<span class="pill soft">{round(confidence * 100)}% confidence</span>' if confidence else ""
    H(f"""<div class="dz-head"><div><div class="dz-name">{d['name_te'] if te else d['name']}</div>
<span class="muted">{data.CROPS[d['crop']] if te else d['crop']} · {d['type']}</span></div>{conf}</div>
<div class="grid2"><div class="box"><b>{'ఎందుకు వస్తుంది' if te else 'Why it happens'}</b>{d['cause_te'] if te else d['cause']}</div>
<div class="box"><b>{'లక్షణాలు' if te else 'Symptoms to check'}</b>{d['symptoms_te'] if te else d['symptoms']}</div></div>""")
    cards = []
    for i, t in enumerate(diseases.plan_for(d, acres)):
        icon = "🧪" if t["kind"] == "Chemical" else "🌿"
        if t["per"] == "litre":
            qty = (f'<div><small>Per litre</small><b>{fmt(t["dose"], t["unit"])}</b></div>'
                   f'<div><small>Per {tank} L tank</small><b>{fmt(t["per_tank"], t["unit"])}</b></div>'
                   f'<div><small>Tanks · water</small><b>{t["tanks"]:g} · {t["water_total_l"]:g} L</b></div>'
                   f'<div class="total"><small>Total to buy</small><b>{fmt(t["total"], t["unit"])}</b></div>')
        else:
            qty = (f'<div><small>Per acre</small><b>{fmt(t["dose"], t["unit"])}</b></div>'
                   f'<div class="total"><small>Total to buy</small><b>{fmt(t["total"], t["unit"])}</b></div>')
        phi = f'<div class="phi">Stop spraying {t["phi_days"]} days before harvest.</div>' if t["phi_days"] else ""
        cards.append(f"""<div class="treat {'best' if i == 0 else ''}">
<div class="t-name">{icon} {t['product']}</div><span class="pill {'soft' if t['kind'] == 'Organic' else 'grey'}">{t['kind']}{' · Recommended' if i == 0 else ''}</span>
<div class="qty">{qty}</div>
<div><b>Why:</b> {t['reason']}</div><div><b>When:</b> {t['when']}</div><div><b>Repeat:</b> {t['repeat']}</div>
<div><b>How:</b> {t['method']}</div>{phi}</div>""")
    H(f"<h3>{'మందుల ప్రణాళిక' if te else 'Treatment plan'} — {acres:g} {'ఎకరాలు' if te else 'acres'}</h3>"
      f'<div class="treat-grid">{"".join(cards)}</div>')
    prev = "".join(f"<li>{p}</li>" for p in d["prevention_te" if te else "prevention"])
    safety = "".join(f"<li>{p}</li>" for p in diseases.SAFETY["te" if te else "en"])
    H(f"""<div class="grid2"><div class="box"><b>{'నివారణ' if te else 'Prevention'}</b><ul>{prev}</ul></div>
<div class="box"><b>{'భద్రత' if te else 'Spraying safety'}</b><ul>{safety}</ul></div></div>
<p class="muted">Doses come only from the vetted library — the AI never writes doses. Demo values; confirm with your AEO before spraying.</p>""")


# ---------------------------------------------------------------------------
# Farmer Services / My Details (Stages 3-4)
# ---------------------------------------------------------------------------

def page_services(user):
    farmer_view = user["role"] == "farmer"
    if farmer_view:
        fid = user["farmer_id"]
    else:
        with st.container(key="panel_pick"):
            fid = st.selectbox("Farmer", [f["farmer_id"] for f in data.FARMERS],
                               format_func=lambda i: f"{i} · {data.FARMER_INDEX[i]['name']} · {data.FARMER_INDEX[i]['district']}")
    f = data.FARMER_INDEX[fid]
    m = st.columns(4)
    m[0].metric("Farmer", f["name"])
    m[1].metric("District", f["district"])
    m[2].metric("Land", f"{f['total_acres']} acres")
    m[3].metric("Crops", ", ".join(f["crops"]))

    with st.container(key="panel_details"):
        H(f'<p class="muted">Village {f["village"]} · Bank {f["bank"]} · Mobile {auth.mask(f["mobile"])}</p>')
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
                st.markdown("**Raise a new grievance**")
                cat = st.selectbox("Category", data.GRIEVANCE_CATEGORIES)
                desc = st.text_area("Describe the problem")
                if st.form_submit_button("Submit grievance", type="primary"):
                    if not desc.strip():
                        st.error("Please describe the problem.")
                    else:
                        g = {"grievance_id": f"GRV-{2401 + len(data.GRIEVANCES)}", "farmer_id": fid,
                             "farmer_name": f["name"], "district": f["district"], "category": cat,
                             "description": desc.strip(), "status": "Open",
                             "created_on": date.today().isoformat(), "channel": "Web chatbot"}
                        data.GRIEVANCES.append(g)
                        st.success(f"Grievance {g['grievance_id']} registered.")
        with t4:
            w = pd.DataFrame(data.WEATHER[f["district"]])[["date", "condition", "max_c", "min_c", "rain_mm", "humidity"]]
            st.dataframe(w, hide_index=True, width="stretch")
        with t5:
            for c in f["crops"]:
                st.markdown(f"**{c}**")
                for tip in data.ADVISORIES[c]["en"]:
                    st.markdown(f"- {tip}")

    if not farmer_view:
        with st.container(key="panel_all_griev"):
            st.markdown("### All grievances")
            rows = sorted(data.GRIEVANCES, key=lambda g: g["created_on"], reverse=True)
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


# ---------------------------------------------------------------------------
# Claude vs ChatGPT (testing, proposal 2.9)
# ---------------------------------------------------------------------------

def page_compare():
    with st.container(key="panel_ask"):
        st.markdown("## ⚖️ Claude vs ChatGPT")
        H('<p class="muted">Ask the same question to both models and compare the answers side by side.</p>')
        c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
        q = c1.text_input("Question", "రైతు భరోసా పథకం గురించి చెప్పండి")
        if c2.button("Compare", type="primary", width="stretch") and q.strip():
            gathered = assistant.gather(q)
            with ThreadPoolExecutor() as pool:
                results = dict(zip(PROVIDER_LABEL, pool.map(lambda p: ai.answer(p, q, gathered), PROVIDER_LABEL)))
            ss.compare = (gathered, results)
    if ss.get("compare"):
        gathered, results = ss.compare
        H(f'<span class="tag stage">{gathered["stage"]}</span><span class="tag">Intent: {gathered["intent"]}</span>'
          + "".join(f'<span class="tag">{html.escape(s)}</span>' for s in gathered["sources"]))
        cols = st.columns(2)
        for col, (p, r) in zip(cols, results.items()):
            with col, st.container(key=f"panel_{p}"):
                H(f'<h3>{r["model"]}</h3><span class="tag model">{r["latency_ms"]} ms · {r["tokens_out"]} tokens</span>'
                  f'<div style="margin-top:10px">{rich(r["text"])}</div>')

    with st.container(key="panel_tests"):
        c1, c2 = st.columns([4, 1], vertical_alignment="center")
        c1.markdown("### Agreed test scenarios")
        if c2.button("▶ Run all tests", type="primary", width="stretch"):
            with st.spinner("Running scenarios on both models..."):
                ss.eval = run_evaluation()
        if ss.get("eval"):
            summary, rows = ss.eval
            cols = st.columns(2)
            for col, p in zip(cols, PROVIDER_LABEL):
                s = summary[p]
                col.metric(PROVIDER_LABEL[p], f"{s['passed']}/{s['total']} passed", f"avg {s['avg_latency_ms']} ms",
                           delta_color="off")
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        else:
            H(f'<p class="muted">{len(data.TEST_SCENARIOS)} scenarios agreed with the department. '
              'Click Run all tests to score both models.</p>')


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
    with st.container(key="panel_pipe_head"):
        c1, c2 = st.columns([3, 1], vertical_alignment="center")
        c1.markdown("## 📄 Content Pipeline")
        c1.markdown('<p class="muted">Documents move through 11 stages. Only <b>Completed</b> documents can be used '
                    'by the chatbot.</p>', unsafe_allow_html=True)
        role = user["role"]
        if role == "admin":
            role = c2.selectbox("Acting as", list(auth.ROLES), format_func=auth.ROLES.get)
        else:
            c2.markdown(f'<span class="pill soft">Acting as {auth.ROLES[role]}</span>', unsafe_allow_html=True)

    if user["role"] in ("contributor", "admin"):
        with st.expander("➕ Upload a new document"):
            with st.form("upload", clear_on_submit=True):
                title = st.text_input("Title")
                c1, c2 = st.columns(2)
                category = c1.selectbox("Category", ["Circular", "Scheme guideline", "Advisory", "Notification"])
                lang = c2.selectbox("Language", ["te", "en"], format_func={"te": "Telugu", "en": "English"}.get)
                text = st.text_area("Paste the text")
                file = st.file_uploader("…or upload a .txt / .pdf", type=["txt", "pdf"])
                if st.form_submit_button("Upload", type="primary"):
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
                        st.rerun()

    for doc in reversed(pipeline.DOCUMENTS):
        d = pipeline.public(doc)
        done = d["stage"] == pipeline.LAST
        with st.container(key=f"panel_doc_{d['id']}"):
            c1, c2 = st.columns([3, 1], vertical_alignment="center")
            c1.markdown(f"**{d['title']}**")
            c1.markdown(f'<span class="tag">{d["category"]}</span><span class="tag">{"Telugu" if d["source_lang"] == "te" else "English"}</span>',
                        unsafe_allow_html=True)
            c2.markdown(f'<div class="status"><span class="pill {"green" if done else "amber"}">{d["stage_label"]}</span></div>',
                        unsafe_allow_html=True)
            st.progress(d["stage"] / pipeline.LAST, text=f"Stage {d['stage'] + 1} of {pipeline.LAST + 1}")
            if not done:
                actor = d["next_actor"]
                allowed = role == "admin" or actor == "system" or actor == role
                who = "Bharat Vistaar platform (automatic)" if actor == "system" else auth.ROLES[actor]
                b1, b2 = st.columns([1, 2], vertical_alignment="center")
                if b1.button(f"Next: {d['next_label']}", key=f"adv_{d['id']}", disabled=not allowed, type="primary"):
                    by = "Bharat Vistaar platform" if actor == "system" else f"{user['name']} ({auth.ROLES[role]})"
                    pipeline.advance(doc, by=by, translate_fn=ai.translate)
                    st.rerun()
                b2.markdown(f'<span class="muted">Done by {who}' + ("" if allowed else " — not your role") + "</span>",
                            unsafe_allow_html=True)
            with st.expander("Text, translation and history"):
                a, b = st.columns(2)
                a.text_area("Original text", d["raw_text"], height=150, disabled=True, key=f"raw_{d['id']}")
                b.text_area("English translation", d.get("translation") or "—", height=150, disabled=True, key=f"tr_{d['id']}")
                st.dataframe(pd.DataFrame(d["history"]), hide_index=True, width="stretch")


# ---------------------------------------------------------------------------
# PMU Dashboard
# ---------------------------------------------------------------------------

def page_dashboard():
    rows = data.QUERY_HISTORY
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    docs = pipeline.DOCUMENTS
    m = st.columns(6)
    m[0].metric("Total queries", len(rows))
    m[1].metric("Last 7 days", sum(r["date"] >= week_ago for r in rows))
    m[2].metric("Telugu share", f"{round(100 * sum(r['lang'] == 'te' for r in rows) / max(1, len(rows)))}%")
    m[3].metric("Farmers onboarded", len(data.FARMERS))
    m[4].metric("Docs published", f"{sum(d['stage'] == pipeline.LAST for d in docs)} / {len(docs)}")
    m[5].metric("Open grievances", sum(g["status"] != "Resolved" for g in data.GRIEVANCES))

    by_day = Counter(r["date"] for r in rows)
    with st.container(key="panel_days"):
        st.markdown("### Queries per day")
        st.bar_chart(pd.DataFrame({"queries": [by_day[d] for d in sorted(by_day)]}, index=sorted(by_day)).tail(30),
                     color="#1f7a3e", height=220)
    cols = st.columns(3)
    for col, key, title in zip(cols, ("intent", "channel", "district"), ("By topic", "By channel", "By district")):
        counts = Counter(r[key] for r in rows if r[key] != "Unknown").most_common(8)
        with col, st.container(key=f"panel_{key}"):
            st.markdown(f"### {title}")
            st.bar_chart(pd.DataFrame(counts, columns=[key, "queries"]).set_index(key), horizontal=True,
                         color="#1f7a3e", height=260)

    with st.container(key="panel_tracker"):
        st.markdown("### Integration tracker")
        st.dataframe(pd.DataFrame(data.TRACKER), hide_index=True, width="stretch")
    with st.container(key="panel_issues"):
        st.markdown("### Risks & issues register")
        st.dataframe(pd.DataFrame(data.ISSUES), hide_index=True, width="stretch")


# ---------------------------------------------------------------------------
# How it works
# ---------------------------------------------------------------------------

def page_about():
    with st.container(key="panel_about"):
        st.markdown("""
## ℹ️ How it works

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

H(CSS)
user = current_user()
if not user:
    ss.pop("token", None)
    auth_screen()
else:
    page = header(user)
    staff = user["role"] != "farmer"
    with st.container(key="content"):
        if page == "Farmer Chat":
            page_chat(user)
        elif page == "Crop Doctor":
            page_doctor()
        elif page == "Farmer Services":
            page_services(user)
        elif page == "Claude vs ChatGPT" and staff:
            page_compare()
        elif page == "Content Pipeline" and staff:
            page_pipeline(user)
        elif page == "PMU Dashboard" and staff:
            page_dashboard()
        else:
            page_about()
