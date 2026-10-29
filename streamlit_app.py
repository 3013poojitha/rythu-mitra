"""Streamlit version of Rythu Mitra (Telangana x Bharat Vistaar prototype).

Run locally:   streamlit run streamlit_app.py
It reuses the same Python logic as the FastAPI backend (backend/app/*), so the
chatbot, login, Crop Doctor and pipeline behave exactly the same. The look
matches the React app: colours in .streamlit/config.toml, layout in CSS below.
"""
import base64
import html
import inspect
import io
import json
import os
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

# API keys: from backend/.env locally, or from Streamlit Cloud "Secrets". Must load before importing ai.
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "backend" / ".env")
try:
    for k in ("AI_MODE", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "CLAUDE_MODEL", "OPENAI_MODEL", "GEMINI_MODEL"):
        if k in st.secrets:
            os.environ[k] = str(st.secrets[k])
except Exception:  # no secrets file - fine, stays in mock mode
    pass

# Streamlit reruns this file after a code update but keeps the old backend modules in memory, so the
# new file could call something the old modules do not have. When the backend files change, load them fresh.
_code_stamp = max(p.stat().st_mtime for p in (ROOT / "backend" / "app").glob("*.py"))
if "app" in sys.modules and getattr(sys.modules["app"], "_code_stamp", None) != _code_stamp:
    for _name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
        del sys.modules[_name]
from app import ai, applications, assistant, auth, consent, data, diseases, history, media, pipeline, profiles, seasons, terms, today  # noqa: E402
from app import report as farm_report  # noqa: E402  (this file has its own report() for Crop Doctor)
sys.modules["app"]._code_stamp = _code_stamp

st.set_page_config(page_title="Rythu Mitra - Telangana x Bharat Vistaar", page_icon="🌾", layout="wide")

PROVIDER_LABEL = {"claude": "Claude", "gpt": "ChatGPT"}  # compared side by side on the test page
MODEL_CHOICES = {**PROVIDER_LABEL, "gemini": "Gemini"}  # chat and Crop Doctor
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
/* App name, user menu and tabs stay at the top while the page scrolls */
[data-testid="stLayoutWrapper"]:has(> .st-key-sticky_head) { position: sticky; top: 0; z-index: 990; }
.st-key-sticky_head { gap: 0; box-shadow: 0 2px 6px rgba(0,0,0,.06); }
.st-key-sticky_head .st-key-nav { margin-top: 0; }
.confirm-box { text-align: center; }
.confirm-box .confirm-icon { font-size: 2.4rem; }
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
.pill.red { background: #ffd6d2; color: #7a1c12; }
.pay-row { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-top: 1px solid #eef1ec; }
.pay-icon { font-size: 1.4rem; }
.pay-main { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.pay-main small { color: #6b7280; }
.pay-amt { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.pill.soft { background: var(--brand-soft); color: var(--brand-dark); }
.st-key-topbar [data-testid="stPopover"] button { background: rgba(255,255,255,.12); border-color: rgba(255,255,255,.25); color: #fff; }
.st-key-topbar [data-testid="stPopover"] button p { color: #fff; font-weight: 600; }
.st-key-today_btn button, .st-key-setup_logout button { background: rgba(255,255,255,.12); border-color: rgba(255,255,255,.25); color: #fff; }
.st-key-today_btn button p, .st-key-setup_logout button p { color: #fff; font-weight: 600; }

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

/* My Details (farmer profile, land & crops) */
.st-key-farmhero { background: linear-gradient(135deg, #145c2c 0%, #1f7a3e 100%); border-radius: 12px; padding: 12px 18px; box-shadow: var(--shadow); }
/* the greeting sits in the middle of the green card (Streamlit text blocks pull the bottom edge up) */
.st-key-farmhero [data-testid="stMarkdown"], .st-key-farmhero [data-testid="stMarkdownContainer"] { margin: 0 !important; }
.st-key-farmhero button { background: #fff !important; color: var(--brand-dark) !important; border-color: #fff !important; }
.st-key-farmhero button p { color: var(--brand-dark) !important; font-weight: 600; }
.farm-who { display: flex; gap: 12px; align-items: center; }
.farm-avatar { width: 44px; height: 44px; border-radius: 50%; background: #ffd77a; color: #145c2c; display: grid; place-items: center; font-size: 20px; font-weight: 700; flex: none; }
.farm-name { color: #fff; font-size: 19px; font-weight: 700; line-height: 1.3; }
.farm-sub { color: #d4ecdb; font-size: 13px; }
.farm-sub .te { color: #ffd77a; }
.unverified { display: inline-block; margin-left: 8px; background: #fff5e0; color: #8a5a00; border-radius: 99px; padding: 1px 10px; font-size: 12px; font-weight: 600; }
.farm-stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.kpi { background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 14px; box-shadow: var(--shadow); }
.kpi small { display: block; color: var(--muted); font-size: 12px; }
.kpi b { display: block; font-size: 24px; color: var(--brand-dark); line-height: 1.3; }
.kpi b.txt { font-size: 16px; }
.kpi .unit { font-size: 14px; color: var(--muted); }
.crop-chips { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.crop-chips span { background: var(--brand-soft); color: var(--brand-dark); border-radius: 99px; padding: 1px 8px; font-size: 12px; font-weight: 600; }
.plot-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; margin-top: 8px; }
.plot-card { display: flex; gap: 12px; border: 1px solid var(--line); border-radius: 10px; padding: 12px; background: #fbfdfb; font-size: 14px; }
.plot-crop { width: 44px; height: 44px; border-radius: 10px; background: var(--brand-soft); display: grid; place-items: center; font-size: 24px; flex: none; }
.plot-top { display: flex; justify-content: space-between; gap: 6px; }
.plot-meta { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 4px; font-size: 12px; color: var(--muted); }
.st-key-panel_farmedit { border-top: 4px solid var(--brand); }
/* page_js() frames are invisible helpers */
.stElementContainer:has(> .stIFrame) { display: none !important; }  /* only page_js() makes these */
/* Floating WhatsApp button (drag anywhere, tap to open the WhatsApp chat) */
.wa-float { position: fixed; right: 20px; bottom: 20px; z-index: 1000; width: 60px; height: 60px; border-radius: 50%; border: 0; padding: 0; background: #25d366; display: grid; place-items: center; box-shadow: 0 6px 18px rgba(0,0,0,.25); cursor: grab; touch-action: none; user-select: none; }
.wa-float:hover { background: #1ebe5b; }
.wa-float:active { cursor: grabbing; transform: scale(1.06); }
.st-key-wa_open { display: none !important; }
/* Voice pad: big Talk button + record a voice message */
.st-key-voice_pad { background: #fff; border-top: 1px solid var(--line); padding: 12px 14px 4px; gap: 6px; }
.voice-status { font-weight: 600; color: var(--brand-dark); text-align: center; font-size: 14px; }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(197,59,50,.45); } 70% { box-shadow: 0 0 0 16px rgba(197,59,50,0); } 100% { box-shadow: 0 0 0 0 rgba(197,59,50,0); } }
.vm-audio { width: 230px; max-width: 100%; height: 36px; display: block; margin-bottom: 4px; }
/* Chat: photo thumbnails, voice notes, mic button in the chat box */
.msg .thumb { max-width: 180px; border-radius: 10px; display: block; margin-bottom: 6px; }
.voice-note { display: flex; align-items: center; gap: 8px; min-width: 200px; margin-bottom: 4px; }
.voice-note .play { width: 30px; height: 30px; border-radius: 50%; background: #075e54; color: #fff; display: grid; place-items: center; font-size: 12px; flex: none; }
.voice-note .bars { display: flex; align-items: center; gap: 2px; flex: 1; }
.voice-note .bars i { display: block; width: 3px; border-radius: 2px; background: #8aa59b; }
.voice-note small { color: var(--muted); font-size: 11px; }
.msg .transcript { font-size: 12px; font-style: italic; opacity: .8; border-top: 1px dashed rgba(0,0,0,.15); padding-top: 4px; }
[data-testid="stChatInput"] { position: relative; }
.mic-btn { position: absolute; right: 52px; top: 50%; transform: translateY(-50%); width: 34px; height: 34px; border-radius: 50%; border: 0; background: var(--brand-soft); color: var(--brand); display: flex; align-items: center; justify-content: center; padding: 0; cursor: pointer; z-index: 5; }
.mic-btn.rec { background: #c53b32; color: #fff; }
/* Crop Doctor: the photo box reaches down to the bottom of "Your field", the upload area fills it */
[data-testid="stLayoutWrapper"]:has(> .st-key-panel_photo) { flex: 1 1 auto; display: flex; flex-direction: column; }
.st-key-panel_photo { flex: 1 1 auto; }
.st-key-panel_photo [data-testid="stElementContainer"]:has([data-testid="stFileUploader"]) { flex: 1 1 auto; display: flex; flex-direction: column; }
.st-key-panel_photo [data-testid="stFileUploader"] { flex: 1 1 auto; display: flex; flex-direction: column; }
.st-key-panel_photo [data-testid="stFileUploader"] > *:has([data-testid="stFileUploaderDropzone"]),
.st-key-panel_photo [data-testid="stFileUploaderDropzone"] { flex: 1 1 auto; }
/* Upload button and its hint sit together in the middle of the box */
.st-key-panel_photo [data-testid="stFileUploaderDropzone"] { display: flex; flex-direction: column; justify-content: center;
  align-items: center; gap: 8px; text-align: center; }
.st-key-panel_photo [data-testid="stFileUploaderDropzone"] > * { margin: 0 !important; }
.st-key-panel_photo [data-testid="stFileUploaderDropzoneInstructions"] { height: auto !important; min-height: 0 !important;
  width: auto; flex: 0 0 auto !important; justify-content: center; align-items: center; padding: 0 !important; }
.st-key-panel_photo [data-testid="stFileUploaderDropzone"] button { padding: 10px 22px; }
.st-key-panel_photo [data-testid="stFileUploaderDropzone"] button,
.st-key-panel_photo [data-testid="stFileUploaderDropzone"] button * { font-size: 18px !important; font-weight: 600; }
.st-key-panel_photo [data-testid="stFileUploaderDropzoneInstructions"] span { font-size: 15px !important; }.st-key-panel_hist_head { padding-top: 10px !important; padding-bottom: 10px !important; gap: 6px; }
.st-key-panel_hist_head h3 { margin: 0; padding: 0; }
.st-key-panel_hist_head button { min-height: 0; padding: 4px 12px; }
.st-key-panel_hist_head button p { font-size: 14px; }
.st-key-panel_password { max-width: 560px; margin: 24px auto 0; }  /* centred on the page */
.st-key-svc_side { gap: 10px; }
.st-key-svc_side [data-testid="stExpander"] details { border-radius: 12px; background: #fff; }
.st-key-svc_side [data-testid="stExpander"] summary { padding: 14px 14px; }
.st-key-svc_side [data-testid="stExpander"] summary p { font-weight: 700; font-size: 15px; }
.st-key-svc_side [data-testid="stExpander"] summary [data-testid="stIconMaterial"] { display: none; }
.st-key-svc_side [data-testid="stExpander"] summary::after { content: "›"; margin-left: auto; font-size: 24px; line-height: 1;
  color: var(--muted); transition: transform .2s; }
.st-key-svc_side [data-testid="stExpander"] details[open] summary::after { transform: rotate(90deg); color: var(--brand); }
.side-row { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #f0f3ef; }
.st-key-svc_side [data-testid="stExpander"] summary > span { justify-content: flex-start; }
.st-key-svc_side [data-testid="stExpander"] summary [data-testid="stMarkdownContainer"] { text-align: left; }
.side-row .pill { white-space: normal; text-align: center; max-width: 140px; }
/* Below 1000px the right-side rows go under the details and chat, full width */
@media (max-width: 1000px) {
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .st-key-svc_side) { flex-direction: column; }
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .st-key-svc_side) > [data-testid="stColumn"] { width: 100%; flex: 1 1 auto; }
}
.side-row .grow { flex: 1; display: flex; flex-direction: column; }
.st-key-svc_side .weather { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 6px; }
.st-key-svc_side .wday { border: 1px solid var(--line); border-radius: 10px; padding: 8px 2px; display: flex; flex-direction: column;
  align-items: center; font-size: 12px; }
.st-key-svc_side .wicon { font-size: 20px; }
.st-key-svc_side .rain { color: #1565c0; }
.crop-dates { display: flex; flex-wrap: wrap; gap: 6px 12px; align-items: center; margin-top: 6px; font-size: 13px; }
.st-key-setup_page { max-width: 1000px; margin: 0 auto; }
/* Consent screen (once, before the app) */
.st-key-consent_page { max-width: 680px; margin: 0 auto; background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 18px 20px; }
.consent { display: flex; flex-direction: column; gap: 8px; font-size: 15px; line-height: 1.5; }
.consent h2 { text-align: center; margin: 0; padding: 0; font-size: 22px !important; }
.consent h3 { margin: 6px 0 0; padding: 0; font-size: 17px !important; }
.consent p, .consent ul { margin: 0; }
.consent small { color: #5b6b5f; }
.consent-icon { font-size: 2.4rem; text-align: center; }
.consent-keeps { display: flex; flex-direction: column; gap: 6px; }
.consent-keeps div { display: flex; gap: 10px; background: #f5f7f4; border-radius: 10px; padding: 8px 12px; }
.consent-promise { list-style: none; padding: 10px 12px !important; background: var(--brand-soft); border-radius: 10px; }
.apply-info { background: #f5f7f4; border-radius: 10px; padding: 10px 12px; font-size: 13px; margin-bottom: 8px; }
.apply-info p { margin: 0 0 6px; }
.st-key-lib_crop_row { flex-wrap: wrap; }
.st-key-lib_crop_row > div { width: auto !important; flex: 0 1 auto !important; }
.st-key-lib_q input { border-radius: 99px; font-size: 14px; }
.setup-head { text-align: center; }
.setup-head p { max-width: 560px; margin: 6px auto; color: #5b6b5f; }
/* Today's update pop-up */
.today-head { text-align: center; color: #5b6b5f; margin-bottom: 10px; }
.today-weather { display: flex; align-items: center; gap: 14px; background: var(--brand-soft); border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; }
.today-weather b { display: block; font-size: 17px; }
.today-weather small { display: block; color: #5b6b5f; }
.today-wicon { font-size: 2.6rem; line-height: 1; }
.today-h { margin: 14px 0 8px; font-size: 16px; }
.today-lines { display: flex; flex-direction: column; gap: 8px; }
.today-line { display: flex; gap: 10px; align-items: flex-start; padding: 10px 12px; border-radius: 10px; font-size: 15px; line-height: 1.45; background: #f5f7f4; }
.today-line.wait { background: #fff5e0; }
.today-line.do { background: #e9f6ec; }
.today-icon { font-size: 20px; line-height: 1.2; }
.msg-media { display: grid; grid-template-columns: repeat(auto-fill, minmax(84px, 1fr)); gap: 6px; margin-bottom: 6px; max-width: 320px; }
.msg-media .mm { position: relative; }
.msg-media img { width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 8px; display: block; }
.msg-media .mm span { position: absolute; left: 4px; bottom: 4px; background: rgba(0,0,0,.55); border-radius: 6px; padding: 0 4px; font-size: 13px; }
.st-key-doc_thumbs { flex-wrap: wrap; }
.mic-btn.talk { background: var(--brand); color: #fff; animation: pulse 1.4s infinite; }
.st-key-quick_row { flex-wrap: wrap; }
.st-key-quick_row { margin: -4px 0 10px; }
.st-key-quick_row button { border-radius: 99px; min-height: 0; padding: 4px 12px; background: #fff; border-color: var(--brand); color: var(--brand); }
.st-key-quick_row button p { font-size: 13px; }
.st-key-farmer_chat { scroll-margin-top: 140px; }
/* Home chat fits the screen: messages scroll inside, the typing box and mic stay in view */
.st-key-farmer_chat div:has(> .st-key-msgs) { flex: 0 0 auto !important; height: max(300px, calc(100vh - 410px)) !important; }
.st-key-farmer_chat .st-key-msgs { height: 100% !important; }
/* Remedy follow-up inside the chat */
.msg.bot.fu { border-left: 4px solid var(--accent); background: #fffdf6; }
[class*="st-key-bellr_"] { flex-wrap: wrap; }
[class*="st-key-bellr_"] button { border: 1.5px solid var(--brand); border-radius: 99px; background: #fff; min-height: 0; padding: 4px 14px; }
[class*="st-key-bellr_"] button p { color: var(--brand-dark); font-weight: 600; font-size: 13px; }
[class*="st-key-bellr_"] button:hover { background: var(--brand); }
[class*="st-key-bellr_"] button:hover p { color: #fff; }
.hist-photos { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 10px; }
.hist-photo { margin: 0; width: 160px; }
.hist-photo img, .hist-photo .no-photo { width: 160px; height: 120px; object-fit: cover; border-radius: 10px; border: 1px solid var(--line); display: block; }
.hist-photo .no-photo { display: grid; place-items: center; color: var(--muted); background: #f6f7f5; font-size: 13px; }
.hist-photo figcaption { display: flex; justify-content: space-between; font-size: 12px; margin-top: 4px; }
/* Crops grown (crop history timeline) */
[data-testid="stHeaderActionElements"] { display: none !important; }  /* the 🔗 link icon next to headings */
.gantt { border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; background: #fbfdfb; overflow-x: auto; margin-bottom: 8px; }
.g-axis, .g-row { display: flex; align-items: center; gap: 10px; min-width: 560px; }
.g-row { height: 34px; border-top: 1px solid var(--line); }
.g-name { flex: none; width: 82px; font-size: 12px; font-weight: 600; color: var(--muted); }
.g-track { position: relative; flex: 1; height: 100%; }
.g-axis .g-track { height: 22px; }
.g-band { position: absolute; top: 0; height: 100%; display: grid; place-items: center; font-size: 12px; font-weight: 700; color: var(--brand-dark); background: #eef4ec; border-left: 1px solid #d5e0d2; border-radius: 6px 6px 0 0; }
.g-band.odd { background: #e3ede0; }
.g-months { height: 16px; }
.g-months .g-track span { position: absolute; top: 0; text-align: center; font-size: 9px; color: var(--muted); }
.g-bg { position: absolute; top: 0; bottom: 0; background: #f6faf5; border-left: 1px solid #dfe8dc; }
.g-bg.odd { background: #eef4ec; }
.g-bar { position: absolute; top: 5px; height: 24px; border-radius: 6px; font-size: 11px; font-weight: 600; color: #fff; padding: 3px 6px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; box-shadow: 0 1px 2px rgba(0,0,0,.12); }
.g-bar.kharif, .g-legend .kharif { background: #2f8f4e; }
.g-bar.rabi, .g-legend .rabi { background: #c98a1b; }
.g-bar.summer, .g-legend .summer { background: #3a7fc1; }
.g-bar.both, .g-legend .both { background: #2a8f8a; }
.g-bar.now { background-image: repeating-linear-gradient(45deg, rgba(255,255,255,.18) 0 6px, transparent 6px 12px); border-right: 3px solid #ffd77a; }
.g-legend { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 8px; font-size: 11px; color: var(--muted); }
.g-legend i { display: inline-block; width: 12px; height: 12px; border-radius: 3px; vertical-align: -2px; margin-right: 4px; }
.g-legend .now { background: repeating-linear-gradient(45deg, #2f8f4e 0 4px, #6fbf86 4px 8px); }
.season-card { display: flex; gap: 12px; border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; background: #fff; font-size: 14px; }
.season-when { margin-top: 2px; font-size: 13px; color: var(--muted); }
.season-when b { color: var(--ink); }
.st-key-panel_seasonform { border: 1px solid var(--line); border-top: 3px solid var(--brand); border-radius: 12px; padding: 14px; background: #fbfdfb; }
/* Crop health history */
.saved-note { background: var(--brand-soft); color: var(--brand-dark); border-radius: 10px; padding: 10px 14px; font-weight: 600; font-size: 14px; }
.kpi b.warn { color: var(--amber); }
.empty { text-align: center; padding: 30px 10px; color: var(--muted); }
.hist-card { display: flex; gap: 14px; border: 1px solid var(--line); border-radius: 12px; padding: 14px; background: #fff; font-size: 14px; }
.hist-card.pending { border-left: 4px solid var(--accent); }
.hist-date { flex: none; width: 64px; text-align: center; background: var(--brand-soft); border-radius: 10px; padding: 8px 4px; height: fit-content; }
.hist-date b { display: block; color: var(--brand-dark); font-size: 15px; }
.hist-date small { color: var(--muted); font-size: 11px; }
.hist-head { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; align-items: flex-start; }
.hist-title { font-size: 15px; }
.hist-steps { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }
.hist-steps > div { background: #fbfdfb; border: 1px solid var(--line); border-radius: 10px; padding: 8px 10px; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.hist-steps b { font-size: 13px; }
.hist-steps small { font-size: 12px; color: var(--muted); overflow-wrap: anywhere; }
.step-n { width: 20px; height: 20px; border-radius: 50%; background: var(--brand); color: #fff; font-size: 11px; font-weight: 700; display: grid; place-items: center; margin-bottom: 2px; }
.hist-note { font-style: italic; color: var(--ink) !important; }
[class*="st-key-panel_fb_"] { border-top: 3px solid var(--accent); }
@media (max-width: 820px) {
  .hist-steps { grid-template-columns: 1fr 1fr; }
  .hist-card { flex-direction: column; }
  .hist-date { width: auto; display: flex; gap: 8px; justify-content: center; }
}
[class*="st-key-plotrow"] { border: 1px solid var(--line); border-radius: 10px; padding: 8px 12px 12px; background: #fbfdfb; }
/* తెలుగు | English switch: on the green top bar the selected segment is white */
.st-key-lang_top button[data-variant="segmented_control"] { background: rgba(255,255,255,.12) !important; border-color: rgba(255,255,255,.3) !important; min-height: 0; padding: 2px 10px; }
.st-key-lang_top button[data-variant="segmented_control"] p { color: #fff !important; font-size: 13px; }
.st-key-lang_top button[data-variant="segmented_control"][aria-checked="true"] { background: #fff !important; border-color: #fff !important; }
.st-key-lang_top button[data-variant="segmented_control"][aria-checked="true"] p { color: var(--brand-dark) !important; }
.st-key-topright { flex-wrap: wrap; row-gap: 6px; }
.st-key-topright > div { width: auto !important; flex: 0 0 auto !important; }
.st-key-lang_auth { display: flex; justify-content: flex-end; }

@media (max-width: 820px) {
  .st-key-topbar, .st-key-nav, .banner { padding-left: 16px; padding-right: 16px; }
  .st-key-content { padding: 16px 16px 0; }
  .grid2 { grid-template-columns: 1fr; }
  .farm-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
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

# Telugu only: Streamlit's photo upload box has fixed English words, so swap them with CSS
TE_CSS = """
<style>
.st-key-crop_photo [data-testid="stFileUploaderDropzoneInstructions"] span { font-size: 0 !important; }
.st-key-crop_photo [data-testid="stFileUploaderDropzoneInstructions"] span::after { content: "ఫోటో 200MB వరకు · JPG, PNG, WEBP"; font-size: 12px; }
.st-key-crop_photo [data-testid="stFileUploaderDropzone"] button p { font-size: 0 !important; }
.st-key-crop_photo [data-testid="stFileUploaderDropzone"] button p::after { content: "ఫోటో పెట్టండి"; font-size: 14px; }
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


COOKIE = "rythu_token"


def remember_login(token):
    """Keep the login in a browser cookie so refreshing the page does not log out.
    Log out (top-right menu) clears it. It expires with the session (8 hours)."""
    if token:
        value, age = token, auth.SESSION_HOURS * 3600
    else:
        value, age = "", 0
    st.html(f"""<script>document.cookie = "{COOKIE}={value}; path=/; max-age={age}; SameSite=Strict"
        + (location.protocol === "https:" ? "; Secure" : "");</script>""", unsafe_allow_javascript=True)


def current_user():
    """The logged-in user record, or None. After a page refresh Streamlit starts a
    new session, so the login is picked up again from the browser cookie, or from the
    address bar (?s=...) - Streamlit Cloud does not pass cookies to the app."""
    if not ss.get("token") and not ss.get("logged_out"):
        for saved in (st.context.cookies.get(COOKIE), st.query_params.get("s")):
            if isinstance(saved, str) and saved and auth.user_for_token(saved):
                ss.token = saved
                break
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


def seg(label, options, key, labels=None, default=None, on_change=None):
    """Segmented buttons like the React app's .seg control; never returns None."""
    val = st.segmented_control(label, options, key=key, default=default or options[0],
                               format_func=(labels or {}).get if labels else str, on_change=on_change)
    return val or default or options[0]


# ---------------------------------------------------------------------------
# Language: the app opens in Telugu; the తెలుగు | English switch changes every screen
# ---------------------------------------------------------------------------

LANG_COOKIE = "rythu_lang"
TE_MONTHS = ["జనవరి", "ఫిబ్రవరి", "మార్చి", "ఏప్రిల్", "మే", "జూన్", "జులై", "ఆగస్టు", "సెప్టెంబర్", "అక్టోబర్", "నవంబర్", "డిసెంబర్"]


LANG = "te"  # language of this script run, set by init_lang()


def init_lang():
    """Pick the language once per session: the saved cookie, else Telugu. After that the
    session value wins (Streamlit reads cookies only when the session starts)."""
    global LANG
    if ss.get("ui_lang") not in ("te", "en"):
        saved = st.context.cookies.get(LANG_COOKIE)
        ss.ui_lang = saved if saved in ("te", "en") else "te"
    LANG = ss.ui_lang


def is_te():
    return LANG == "te"


def T(en, te):
    """The English or Telugu text, whichever language is switched on."""
    return te if is_te() else en


def V(value):
    """A data value (soil, season, status, ...) in the chosen language; the backend keeps English."""
    return terms.te(value) if is_te() else value


def err(e):
    """A backend error message in the chosen language."""
    return terms.te_error(str(e)) if is_te() else str(e)


def crop_name(c):
    return data.crop_te(c) if is_te() else c


def month_label(m):
    """'2026-10' -> 'Oct 2026' / 'అక్టోబర్ 2026'."""
    if is_te():
        return f"{TE_MONTHS[int(m[5:7]) - 1]} {m[:4]}"
    return datetime.strptime(m, "%Y-%m").strftime(MONTH_FMT)


def day_label(d):
    """A date as '27 Oct' / '27 అక్టోబర్'."""
    return f"{d.day} {TE_MONTHS[d.month - 1]}" if is_te() else f"{d:%d %b}"


def time_label(t):
    if not is_te():
        return f"{t:%I:%M %p}"
    part = "ఉదయం" if t.hour < 12 else "మధ్యాహ్నం" if t.hour < 16 else "సాయంత్రం" if t.hour < 19 else "రాత్రి"
    return f"{part} {(t.hour - 1) % 12 + 1}:{t.minute:02d}"


def pick_lang(key):
    if ss.get(key):
        ss.ui_lang = ss[key]
        ss.save_lang = True


def lang_switch(key):
    """Small తెలుగు | English buttons (top bar, and the login card)."""
    ss[key] = ss.ui_lang  # always show the language that is on now
    st.segmented_control("Language / భాష", ["te", "en"], key=key, format_func={"te": "తెలుగు", "en": "English"}.get,
                         label_visibility="collapsed", on_change=pick_lang, args=(key,))


def remember_lang():
    """Keep the language in a browser cookie (1 year) so a refresh opens in the same language."""
    st.html(f"""<script>document.cookie = "{LANG_COOKIE}={ss.ui_lang}; path=/; max-age=31536000; SameSite=Strict"
        + (location.protocol === "https:" ? "; Secure" : "");</script>""", unsafe_allow_javascript=True)


# ---------------------------------------------------------------------------
# Login, sign up, forgot / reset password
# ---------------------------------------------------------------------------

def auth_screen():
    H(AUTH_CSS)
    hero, card = st.columns([1.2, 1], gap="large")
    with hero:
        if is_te():
            H("""<div class="auth-hero"><div class="logo big">🌾</div>
<h1><span class="te">రైతు మిత్ర</span></h1>
<p>తెలంగాణ వ్యవసాయ శాఖ × భారత్ విస్తార్</p>
<ul><li>తెలుగు, ఇంగ్లీష్‌లో రైతు సహాయకుడు</li><li>ఫోటోతో పంట తెగులు గుర్తింపు, పిచికారీ సలహా</li>
<li>పథకాలు, డబ్బు జమ, ఫిర్యాదుల స్థితి</li><li>సిబ్బంది కోసం సమాచార పైప్‌లైన్, PMU డ్యాష్‌బోర్డ్</li></ul>
<small>నమూనా సమాచారంతో ప్రయోగాత్మక యాప్</small></div>""")
        else:
            H("""<div class="auth-hero"><div class="logo big">🌾</div>
<h1>Rythu Mitra</h1>
<p>Telangana Agriculture Department × Bharat Vistaar</p>
<ul><li>Telugu &amp; English farmer assistant</li><li>Crop disease detection with spray guidance</li>
<li>Scheme, payment and grievance status</li><li>Content pipeline and PMU dashboard for staff</li></ul>
<small>Prototype with dummy data</small></div>""")
    with card, st.container(key="panel_auth"):
        lang_switch("lang_auth")  # a farmer can pick Telugu or English before logging in
        if ss.get("notice"):
            n = ss.pop("notice")  # text, or {"te": ..., "en": ...} that follows the language switch
            st.success(n[ss.ui_lang] if isinstance(n, dict) else n)
        mode = ss.get("auth_mode", "login")
        if mode == "login":
            login_form()
        elif mode == "register":
            register_form()
        else:
            forgot_form()


def go(mode):
    ss.auth_mode = mode


PW_HELP = ("8+ characters with letters and numbers", "కనీసం 8 అక్షరాలు - అక్షరాలు, అంకెలు రెండూ ఉండాలి")


def login_form():
    st.markdown("### " + T("Log in", "లాగిన్"))
    H('<p class="muted">' + T("Farmers use their Farmer ID (e.g. TS1002) or mobile number. Staff use their department user ID.",
                              "రైతులు తమ రైతు ID (ఉదా. TS1002) లేదా మొబైల్ నంబర్ వాడండి. సిబ్బంది తమ శాఖ యూజర్ ID వాడండి.") + "</p>")
    with st.form("login", border=False):
        uid = st.text_input(T("User ID or mobile number", "యూజర్ ID లేదా మొబైల్ నంబర్"))
        pwd = st.text_input(T("Password", "పాస్‌వర్డ్"), type="password")
        if st.form_submit_button(T("Log in", "లాగిన్"), type="primary", width="stretch"):
            try:
                ss.token, _ = auth.login(uid, pwd)
                ss.save_cookie = True
                st.rerun()
            except auth.AuthError as e:
                st.error(err(e))
    # One under the other: the Telugu words are too long to sit side by side on a phone
    st.button(T("Forgot password?", "పాస్‌వర్డ్ మర్చిపోయారా?"), on_click=go, args=("forgot",), type="tertiary")
    st.button(T("New farmer? Create account", "కొత్త రైతా? ఖాతా తెరవండి"), on_click=go, args=("register",), type="tertiary")


def register_form():
    st.markdown("### " + T("Farmer sign-up", "రైతు ఖాతా తెరవండి"))
    choice = st.segmented_control(
        T("Sign-up type", "నమోదు రకం"), ["id", "new"], default="id", key="reg_type", label_visibility="collapsed",
        format_func=lambda c: T("I have a Farmer ID", "నాకు రైతు ID ఉంది") if c == "id" else T("New farmer (no Farmer ID)", "కొత్త రైతు (ID లేదు)"))
    if choice == "new":
        register_new_form()
        return
    H('<p class="muted">' + T("Use your Farmer ID and the mobile number on your department record.",
                              "మీ రైతు ID, శాఖ రికార్డులో ఉన్న మొబైల్ నంబర్ వాడండి.") + "</p>")
    with st.form("signup", border=False):
        fid = st.text_input(T("Farmer ID", "రైతు ID"), placeholder=T("e.g. TS1005", "ఉదా. TS1005"))
        mob = st.text_input(T("Registered mobile number", "నమోదైన మొబైల్ నంబర్"))
        p1 = st.text_input(T("New password", "కొత్త పాస్‌వర్డ్"), type="password", help=T(*PW_HELP))
        p2 = st.text_input(T("Confirm password", "పాస్‌వర్డ్ మళ్లీ రాయండి"), type="password")
        if st.form_submit_button(T("Create account", "ఖాతా తెరవండి"), type="primary", width="stretch"):
            try:
                u = auth.register(fid, mob, p1, p2)
                ss.notice = T(f"Account created for {u['name']}. Log in with user ID {u['user_id']}.",
                              f"{u['name']} గారికి ఖాతా తెరిచాము. యూజర్ ID {u['user_id']} తో లాగిన్ చేయండి.")
                go("login")
                st.rerun()
            except auth.AuthError as e:
                st.error(err(e))
    st.button(T("← Back to log in", "← లాగిన్‌కు వెనక్కి"), on_click=go, args=("login",), type="tertiary")


def register_new_form():
    """A new farmer with no department Farmer ID: name, mobile, district and password. The app gives
    them a Farmer ID (not yet verified by the AEO); next they agree to consent and fill in their details."""
    H('<p class="muted">' + T("No Farmer ID yet? Sign up here. You get a new Farmer ID; your AEO verifies your details later.",
                              "రైతు ID ఇంకా లేదా? ఇక్కడ నమోదు చేసుకోండి. మీకు కొత్త రైతు ID వస్తుంది; మీ వివరాలను తర్వాత మీ AEO పరిశీలిస్తారు.") + "</p>")
    with st.form("signup_new", border=False):
        name = st.text_input(T("Full name", "పూర్తి పేరు"))
        mob = st.text_input(T("Mobile number", "మొబైల్ నంబర్"), max_chars=10, placeholder=T("10-digit mobile", "10 అంకెల మొబైల్ నంబర్"))
        district = st.selectbox(T("District", "జిల్లా"), list(data.DISTRICTS), index=None,
                                format_func=lambda d: data.DISTRICTS[d] if is_te() else d, placeholder=T("Choose…", "ఎంచుకోండి…"))
        p1 = st.text_input(T("New password", "కొత్త పాస్‌వర్డ్"), type="password", help=T(*PW_HELP))
        p2 = st.text_input(T("Confirm password", "పాస్‌వర్డ్ మళ్లీ రాయండి"), type="password")
        if st.form_submit_button(T("Create account", "ఖాతా తెరవండి"), type="primary", width="stretch"):
            try:
                u = auth.register_new(name, mob, district, p1, p2)
                ss.notice = {"en": f"Account created for {u['name']}. Your new Farmer ID is {u['user_id']}. "
                                   "Log in with it or with your mobile number.",
                             "te": f"{u['name']} గారి ఖాతా తెరవబడింది. మీ కొత్త రైతు ID {u['user_id']}. "
                                   "దీనితో లేదా మీ మొబైల్ నంబర్‌తో లాగిన్ చేయండి."}
                go("login")
                st.rerun()
            except auth.AuthError as e:
                st.error(err(e))
    st.button(T("← Back to log in", "← లాగిన్‌కు వెనక్కి"), on_click=go, args=("login",), type="tertiary", key="back_new")


def forgot_form():
    if not ss.get("reset_uid"):
        st.markdown("### " + T("Forgot password", "పాస్‌వర్డ్ మర్చిపోయారా?"))
        H('<p class="muted">' + T("Enter your user ID. We will send a 6-digit code to your registered mobile.",
                                  "మీ యూజర్ ID రాయండి. మీ మొబైల్‌కు 6 అంకెల కోడ్ పంపుతాము.") + "</p>")
        with st.form("forgot", border=False):
            fuid = st.text_input(T("User ID", "యూజర్ ID"))
            if st.form_submit_button(T("Send code", "కోడ్ పంపండి"), type="primary", width="stretch"):
                try:
                    res = auth.forgot_password(fuid)
                    ss.reset_uid, ss.demo_otp, ss.sent_to = fuid, res["demo_otp"], res["sent_to"]
                    st.rerun()
                except auth.AuthError as e:
                    st.error(err(e))
    else:
        st.markdown("### " + T("Reset password", "కొత్త పాస్‌వర్డ్ పెట్టండి"))
        H('<p class="muted">' + T(f"Code sent to mobile {ss.sent_to}. It expires in {auth.OTP_MINUTES} minutes.",
                                  f"మొబైల్ {ss.sent_to} కు కోడ్ పంపాము. ఇది {auth.OTP_MINUTES} నిమిషాలు పనిచేస్తుంది.") + "</p>"
          + '<div class="demo-otp">' + T("Demo only — no real SMS is sent. Your code is",
                                         "డెమో మాత్రమే — నిజమైన SMS రాదు. మీ కోడ్") + f" <b>{ss.demo_otp}</b></div>")
        with st.form("reset", border=False):
            otp = st.text_input(T("6-digit code", "6 అంకెల కోడ్"))
            r1 = st.text_input(T("New password", "కొత్త పాస్‌వర్డ్"), type="password", help=T(*PW_HELP))
            r2 = st.text_input(T("Confirm new password", "కొత్త పాస్‌వర్డ్ మళ్లీ రాయండి"), type="password")
            if st.form_submit_button(T("Reset password", "పాస్‌వర్డ్ మార్చండి"), type="primary", width="stretch"):
                try:
                    auth.reset_password(ss.reset_uid, otp, r1, r2)
                    ss.pop("reset_uid")
                    ss.notice = T("Password changed. Log in with your new password.",
                                  "పాస్‌వర్డ్ మారింది. కొత్త పాస్‌వర్డ్‌తో లాగిన్ చేయండి.")
                    go("login")
                    st.rerun()
                except auth.AuthError as e:
                    st.error(err(e))
    st.button(T("← Back to log in", "← లాగిన్‌కు వెనక్కి"), on_click=lambda: (ss.pop("reset_uid", None), go("login")),
              type="tertiary")


# ---------------------------------------------------------------------------
# Top bar and tabs (same as the React header)
# ---------------------------------------------------------------------------

TABS = [("Farmer Chat", None), ("Crop Doctor", None), ("Farmer Services", "🏠 Home"),
        ("Claude vs ChatGPT", None), ("Content Pipeline", None), ("PMU Dashboard", None)]
# History and How the app works open from the user menu (top right), not the tab bar
MENU_PAGES = {"details": "My details", "history": "History", "about": "How the app works", "password": "Change password"}
STAFF_TABS = {"Claude vs ChatGPT", "Content Pipeline", "PMU Dashboard"}
FARMER_HIDDEN = {"Farmer Chat"}  # farmers chat right under their details on My Details
TAB_TE = {"Farmer Chat": "రైతు చాట్", "Crop Doctor": "పంట వైద్యుడు", "Farmer Services": "రైతు సేవలు",
          "🏠 Home": "🏠 ముఖ్య పేజీ"}


def page_js(code, wait_for=None):
    """Run JavaScript in the app page itself. A hidden component frame (which Streamlit
    always runs, on every rerun) adds the code to the page as a <script>. With wait_for
    (a CSS selector) the code waits until that element is on the page (up to 4 seconds)."""
    if wait_for:
        code = (f"(function run(n) {{ if (!document.querySelector({json.dumps(wait_for)})) "
                f"{{ if (n < 40) setTimeout(() => run(n + 1), 100); return; }} {code} }})(0);")
    components.html(f"""<script>
const d = window.parent.document, s = d.createElement('script');
s.textContent = {json.dumps(code)};
d.head.appendChild(s); s.remove();
</script>""", height=0)


def open_whatsapp():
    """Floating WhatsApp button: open the chat in WhatsApp style (farmers: on My Details)."""
    ss.pop("view", None)
    farmer = (current_user() or {}).get("role") == "farmer"
    ss.page = "Farmer Services" if farmer else "Farmer Chat"
    ss.wa_mode = True
    ss.wa_scroll = farmer


def whatsapp_button():
    """A green WhatsApp button that floats over every page. Drag it anywhere (the spot is
    remembered); tap it to open the chat in WhatsApp style. It clicks a hidden Streamlit button."""
    page_js(SAY_JS)  # rmSay / rmQuiet for reading aloud (the mic welcome uses them)
    st.button("WhatsApp", key="wa_open", on_click=open_whatsapp)
    label = T("Chat on WhatsApp", "వాట్సాప్‌లో మాట్లాడండి")
    page_js(f"""
(() => {{
  const KEY = 'rythu_wa_pos', SIZE = 60;
  let b = document.getElementById('wa-float');
  if (!b) {{
    b = document.createElement('button'); b.id = 'wa-float'; b.className = 'wa-float';
    b.innerHTML = '<svg viewBox="0 0 32 32" width="34" height="34"><path fill="#fff" d="M16 3C8.8 3 3 8.7 3 15.8c0 2.3.6 4.5 1.8 6.5L3 29l6.9-1.8c1.9 1 4 1.6 6.1 1.6 7.2 0 13-5.7 13-12.9C29 8.7 23.2 3 16 3zm0 23.6c-1.9 0-3.8-.5-5.4-1.5l-.4-.2-4.1 1.1 1.1-4-.3-.4c-1.1-1.7-1.7-3.7-1.7-5.7C5.2 9.9 10 5.2 16 5.2S26.8 9.9 26.8 15.8 22 26.6 16 26.6zm5.9-8c-.3-.2-1.9-.9-2.2-1-.3-.1-.5-.2-.7.2-.2.3-.8 1-1 1.2-.2.2-.4.2-.7.1-.3-.2-1.4-.5-2.6-1.6-1-.9-1.6-1.9-1.8-2.3-.2-.3 0-.5.1-.7l.5-.6c.2-.2.2-.3.3-.6.1-.2 0-.4 0-.6l-1-2.4c-.3-.6-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.4-.3.3-1.2 1.1-1.2 2.7s1.2 3.2 1.4 3.4c.2.2 2.4 3.6 5.8 5 .8.4 1.5.6 2 .7.8.3 1.6.2 2.2.1.7-.1 1.9-.8 2.2-1.5.3-.7.3-1.4.2-1.5-.1-.2-.3-.3-.6-.4z"/></svg>';
    document.body.appendChild(b);
    const clamp = (p) => ({{ x: Math.min(Math.max(8, p.x), innerWidth - SIZE - 8), y: Math.min(Math.max(8, p.y), innerHeight - SIZE - 8) }});
    const place = (p) => {{ if (p) {{ p = clamp(p); b.style.left = p.x + 'px'; b.style.top = p.y + 'px'; b.style.right = b.style.bottom = 'auto'; }} }};
    try {{ place(JSON.parse(localStorage.getItem(KEY))); }} catch (e) {{}}
    let d = null;
    b.addEventListener('pointerdown', (e) => {{ const r = b.getBoundingClientRect(); d = {{ dx: e.clientX - r.left, dy: e.clientY - r.top, x0: e.clientX, y0: e.clientY, moved: false }}; b.setPointerCapture(e.pointerId); }});
    b.addEventListener('pointermove', (e) => {{ if (!d) return; if (Math.abs(e.clientX - d.x0) + Math.abs(e.clientY - d.y0) > 6) d.moved = true; if (d.moved) place({{ x: e.clientX - d.dx, y: e.clientY - d.dy }}); }});
    b.addEventListener('pointerup', () => {{
      if (!d) return; const moved = d.moved; d = null;
      if (moved) {{ const r = b.getBoundingClientRect(); try {{ localStorage.setItem(KEY, JSON.stringify({{ x: r.left, y: r.top }})); }} catch (e) {{}} return; }}
      document.querySelector('.st-key-wa_open button')?.click();
    }});
    addEventListener('resize', () => {{ const r = b.getBoundingClientRect(); if (b.style.left) place({{ x: r.left, y: r.top }}); }});
  }}
  b.title = b.ariaLabel = {json.dumps(label)};
}})();
""")


def log_out(notice=None):
    auth.logout(ss.pop("token", None))
    lang = ss.ui_lang
    ss.clear()
    ss.ui_lang = lang  # the login screen stays in the same language
    ss.logged_out = True  # don't log straight back in from the old cookie
    if notice:
        ss.notice = notice  # shown on the login screen
    st.rerun()


def confirm_logout():
    """'Do you want to log out?' box in the middle of the page."""
    def box():
        H('<div class="confirm-box"><div class="confirm-icon">🚪</div><p>'
          + T("Do you want to log out of Rythu Mitra?", "మీరు రైతు మిత్ర నుండి లాగ్ అవుట్ అవ్వాలనుకుంటున్నారా?") + "</p></div>")
        with st.container(horizontal=True, horizontal_alignment="center", gap="small"):
            if st.button(T("Cancel", "రద్దు చేయండి")):
                st.rerun()
            if st.button(T("Log out", "లాగ్ అవుట్"), type="primary"):
                log_out()
    st.dialog(T("Log out?", "లాగ్ అవుట్ అవ్వాలా?"), width="small")(box)()


def header(user):
    whatsapp_button()
    if ss.pop("close_menu", False):
        # A menu item opened its own page: close the user menu so the page is not covered
        page_js("if (document.querySelector('[data-testid=stPopoverBody]')) "
                "[...document.querySelectorAll('.st-key-topright [data-testid=stPopover] button')].pop()?.click();")
    if ss.pop("ask_logout", False):
        # Close the user menu so only the "Log out?" box is on screen
        page_js("if (document.querySelector('[data-testid=stPopoverBody]')) "
                "[...document.querySelectorAll('.st-key-topright [data-testid=stPopover] button')].pop()?.click();")
        confirm_logout()
    elif user["role"] == "farmer":
        # Today's update opens by itself after the first login of the day (and from the 📅 button)
        if not ss.get("today_checked"):
            ss.today_checked = True
            if not today.seen_today(user["farmer_id"]):
                ss.show_today = True
        if ss.pop("show_today", False):
            today.mark_seen(user["farmer_id"])
            today_update(user)
    status = ai.status()
    head = st.container(key="sticky_head")
    with head, st.container(key="topbar"):
        left, right = st.columns([2.6, 2.4], vertical_alignment="center")
        title = ('<span class="te" style="margin:0">రైతు మిత్ర</span>' if is_te()
                 else 'Rythu Mitra')
        sub = T("Telangana Agriculture Dept × Bharat Vistaar · Prototype with dummy data",
                f"{terms.UI['Telangana Agriculture Dept × Bharat Vistaar']} · {terms.UI['Prototype with dummy data']}")
        left.markdown(f"""<div class="brand"><div class="logo">🌾</div><div>
<div class="brand-title">{title}</div>
<div class="brand-sub">{sub}</div></div></div>""", unsafe_allow_html=True)
        # తెలుగు | English switch, bell and user menu in one row that wraps on a phone
        with right, st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center",
                                 gap="small", key="topright"):
            # Mock / Live AI is shown in the yellow line under the tabs, not here
            lang_switch("lang_top")
            if user["role"] == "farmer":
                st.button("📅 " + T("Today", "ఈరోజు"), key="today_btn", help=T("Today's update", "ఈరోజు సమాచారం"),
                          on_click=lambda: ss.update(show_today=True))
                bell(user)
            with st.popover(f"👤 {user['name']}", width="content"):
                st.markdown(f"**{user['user_id']}**  \n{V(auth.ROLES[user['role']])} · {T('Mobile', 'మొబైల్')} "
                            f"{auth.mask(user['mobile'])}")
                if user["role"] == "farmer" and st.button("👤 " + T("My details", "నా వివరాలు"), width="stretch"):
                    ss.view = "details"  # details, land and crops, with Edit
                    ss.pop("editing", None)
                    ss.close_menu = True
                    st.rerun()
                if st.button("🔑 " + T("Change password", "పాస్‌వర్డ్ మార్చండి"), width="stretch"):
                    ss.view = "password"  # opens as its own page, like My history
                    ss.close_menu = True
                    st.rerun()
                label = "📜 " + (T("My history", "నా చరిత్ర") if user["role"] == "farmer" else T("Crop history", "పంట చరిత్ర"))
                if st.button(label, width="stretch"):
                    ss.view = "history"
                    ss.close_menu = True
                    st.rerun()
                if st.button(T("How the app works", "యాప్ ఎలా పనిచేస్తుంది"), width="stretch"):
                    ss.view = "about"
                    ss.close_menu = True
                    st.rerun()
                if st.button("🚪 " + T("Log out", "లాగ్ అవుట్"), width="stretch"):
                    ss.ask_logout = True
                    st.rerun()

    staff = user["role"] != "farmer"
    names = [t for t, _ in TABS if staff or t not in STAFF_TABS | FARMER_HIDDEN]
    if not staff:  # farmers land on their own details first
        names.remove("Farmer Services")
        names.insert(0, "Farmer Services")
    labels = {t: (fl if not staff and fl and t == "Farmer Services" else t) for t, fl in TABS}
    if is_te():  # staff-only tabs stay English
        labels = {t: TAB_TE.get(lbl, lbl) for t, lbl in labels.items()}
    # Remember the open tab in the address bar (?page=...) so a refresh stays on it
    slugs = {"Farmer Chat": "chat", "Crop Doctor": "doctor", "Farmer Services": "home", "Claude vs ChatGPT": "compare",
             "Content Pipeline": "pipeline", "PMU Dashboard": "dashboard"}
    if "page" not in ss:
        if st.query_params.get("page") in MENU_PAGES and (st.query_params["page"] != "details" or not staff):
            ss.view = st.query_params["page"]
        wanted = next((n for n, sl in slugs.items() if sl == st.query_params.get("page")), None)
        if wanted in names:
            ss.page = wanted
    # A page opened from the user menu shows as its own highlighted tab, so the bar says where you are
    menu_page = MENU_PAGES.get(ss.get("view")) if ss.get("view") != "details" or not staff else None
    if menu_page:
        names = names + [menu_page]
        labels[menu_page] = {
            "My details": "👤 " + T("My details", "నా వివరాలు"),
            "History": "📜 " + (T("Crop history", "పంట చరిత్ర") if staff else T("My history", "నా చరిత్ర")),
            "Change password": "🔑 " + T("Change password", "పాస్‌వర్డ్ మార్చండి"),
            "How the app works": "ℹ️ " + T("How the app works", "యాప్ ఎలా పనిచేస్తుంది"),
        }[menu_page]
        ss.page = menu_page
    elif ss.get("page") not in names:  # just left a menu page with its Back button
        ss.page = names[0]
    with head, st.container(key="nav"):
        page = st.radio("Page", names, horizontal=True, label_visibility="collapsed", format_func=labels.get, key="page",
                        on_change=lambda: ss.pop("view", None))  # picking a tab leaves the History page
    if ss.get("view") in MENU_PAGES:
        page = MENU_PAGES[ss.view]
    st.query_params["page"] = ss.view if page in MENU_PAGES.values() else slugs[page]
    if all(p["mode"] == "mock" for p in status.values()) and page != "How the app works":  # no AI key at all
        H('<div class="banner">' + T(
            "Running in <b>Mock AI mode</b> — no API keys needed. Answers come from dummy data "
            "with simulated model replies. See <b>How the app works</b> in the menu at the top right.",
            "యాప్ <b>మాక్ AI మోడ్</b> లో నడుస్తోంది — API కీలు అవసరం లేదు. సమాధానాలు నమూనా సమాచారం నుండి వస్తాయి. "
            "వివరాలకు పైన కుడివైపు మెనూలో <b>యాప్ ఎలా పనిచేస్తుంది</b> చూడండి.") + "</div>")
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
WELCOME = {"te": "నమస్కారం! నేను రైతు మిత్ర 🌾\nమార్కెట్ ధరలు, వాతావరణం, పథకాలు, పంట సలహా గురించి తెలుగులో లేదా "
                 "ఇంగ్లీష్‌లో అడగండి. జబ్బు పడిన మొక్క ఫోటో కోసం **పంట వైద్యుడు** వాడండి.",
           "en": "Namaskaram! I am Rythu Mitra 🌾\nAsk me about mandi prices, weather, schemes, crop advice — "
                 "in Telugu or English. For a photo of a sick plant, use **Crop Doctor**."}
# Tags under a chat reply (where the answer came from)
STAGE_TE = {"Stage 1 - Central data": "దశ 1 - కేంద్ర సమాచారం", "Stage 2 - State content": "దశ 2 - రాష్ట్ర సమాచారం",
            "Stage 3 - Personalised (login needed)": "దశ 3 - మీ వివరాలు (లాగిన్ అవసరం)",
            "Stage 4 - Deep integration (land & crop data)": "దశ 4 - మీ భూమి & పంట వివరాలు"}
SOURCE_TE = {"Agmarknet mandi prices (dummy)": "Agmarknet మార్కెట్ ధరలు (నమూనా)",
             "IMD district forecast (dummy)": "IMD జిల్లా వాతావరణ సూచన (నమూనా)",
             "Central scheme guidelines (dummy)": "కేంద్ర పథకం నియమాలు (నమూనా)",
             "State scheme guidelines (dummy)": "రాష్ట్ర పథకం నియమాలు (నమూనా)",
             "Scheme directory (dummy)": "పథకాల జాబితా (నమూనా)", "ICAR crop advisory (dummy)": "ICAR పంట సలహా (నమూనా)",
             "Land & crop records (dummy)": "భూమి & పంట రికార్డులు (నమూనా)",
             "Scheme application API (dummy)": "పథకం దరఖాస్తు API (నమూనా)",
             "DBT benefit status API (dummy)": "DBT డబ్బు జమ స్థితి API (నమూనా)",
             "Grievance redressal API (dummy)": "ఫిర్యాదుల పరిష్కారం API (నమూనా)",
             "Bhu Bharathi land records (dummy)": "భూ భారతి భూమి రికార్డులు (నమూనా)"}


def source_label(s):
    if not is_te():
        return s
    if s.startswith("State circular: "):
        return "రాష్ట్ర సర్క్యులర్: " + s.removeprefix("State circular: ")
    return SOURCE_TE.get(s, s)


# ---- Remedy follow-up asked inside the chat: did you use it, when, did it work? ----

FU_REASONS = [("Could not afford it", "కొనలేకపోయాను"), ("Not available in the shop", "దుకాణంలో దొరకలేదు"),
              ("Used something else", "వేరే మందు వాడాను"), ("Problem went away on its own", "దానంతట అదే తగ్గింది"),
              ("Waiting to confirm with AEO", "AEO తో నిర్ధారించాలి"), ("Other", "ఇతర కారణం")]
FU_FIELD = {"used": "used", "product": "product", "when": "applied_on", "result": "result", "reason": "reason"}


def fu_days(rec):
    return (date.today() - date.fromisoformat(rec["created_on"][:10])).days


def fu_intro(rec, te):
    d = fu_days(rec)
    when = (("ఈరోజు" if te else "Today") if d <= 0 else ("నిన్న" if te else "Yesterday") if d == 1
            else (f"{d} రోజుల క్రితం" if te else f"{d} days ago"))
    product = terms.medicine(rec["remedies"][0]["product"], te)
    if te:
        return f"📝 **మందు పనిచేసిందా?**\n{when} మీ {data.crop_te(rec['crop'])} పంటలో **{rec['disease_te']}** కనిపించింది. మేము **{product}** వాడమని సూచించాము."
    return f"📝 **Quick check on your crop**\n{when} we found **{rec['disease']}** on your {rec['crop']} and suggested **{product}**."


def fu_step(name, rec, te):
    """(question, [(value, label)]) for one step of the follow-up."""
    if name == "used":
        return ("మీరు ఆ మందు వాడారా?" if te else "Did you use the remedy?",
                [("yes", "✅ వాడాను" if te else "✅ Used it"), ("partly", "🌓 కొంత వాడాను" if te else "🌓 Used partly"),
                 ("no", "❌ వాడలేదు" if te else "❌ Did not use")])
    if name == "product":
        return ("ఏ మందు వాడారు?" if te else "Which one did you use?",
                [(m["product"], f'{"🌿" if m["kind"] == "Organic" else "🧪"} {terms.medicine(m["product"], te)}') for m in rec["remedies"]]
                + [("Something else", "వేరే మందు" if te else "Something else")])
    if name == "when":
        since, spotted = fu_days(rec), date.fromisoformat(rec["created_on"][:10])
        times = [(0, "Today", "ఈరోజు"), (1, "Yesterday", "నిన్న"), (3, "This week", "ఈ వారం"),
                 (8, "Last week", "గత వారం"), (16, "Earlier", "అంతకు ముందు")]
        return ("ఎప్పుడు పిచికారీ చేశారు?" if te else "When did you spray?",
                [(max(date.today() - timedelta(days=n), spotted).isoformat(), t if te else en) for n, en, t in times if n <= since])
    if name == "result":
        return ("ఫలితం ఎలా ఉంది?" if te else "How did it work?",
                [("cured", "✅ పూర్తిగా తగ్గింది" if te else "✅ Cured"), ("improved", "👍 మెరుగుపడింది" if te else "👍 Improved"),
                 ("no_change", "➖ మార్పు లేదు" if te else "➖ No change"), ("worse", "👎 ఎక్కువైంది" if te else "👎 Got worse")])
    return ("ఎందుకు వాడలేదు?" if te else "Why didn't you use it?", [(en, t if te else en) for en, t in FU_REASONS])


def fu_next(name, value, rec):
    if name == "used":
        return "reason" if value == "no" else "product" if len(rec["remedies"]) > 1 else "when"
    return {"product": "when", "when": "result"}.get(name)


def both(make):
    """A chat text in both languages, so it follows the language switch."""
    return {"te": make(True), "en": make(False)}


def msg_text(m):
    return m["tx"][LANG] if "tx" in m else m["text"]


def today_update(user):
    """📅 Today's update: weather, watering, spraying and crop work due today, with Read aloud and Done."""
    lang = ss.ui_lang
    te = lang == "te"
    u = today.build(user["farmer_id"])
    if lang == "te":
        ai.speak_later(today.speech(u, "te"), "te")  # start the Telugu voice now, so Read aloud is quick

    def lines(items):
        return "".join(f'<div class="today-line {x["tone"]}"><span class="today-icon">{x["icon"]}</span>'
                       f'<span>{html.escape(x[lang])}</span></div>' for x in items)

    def box():
        w = u["weather"]
        place = u["district_te"] if te else u["district"]
        d = date.fromisoformat(u["date"])
        top = f'<div class="today-head"><small>{day_label(d)} {d.year} · 📍 {place}</small></div>'
        if w:
            tom = w["tomorrow_te" if te else "tomorrow_en"]
            top += (f'<div class="today-weather"><span class="today-wicon">{w["icon"]}</span><div>'
                    f'<b>{html.escape(w[lang])}</b>{f"<small>{html.escape(tom)}</small>" if tom else ""}</div></div>')
        H(top + f'<div class="today-lines">{lines(u["weather_lines"])}</div>'
          + f'<h4 class="today-h">🌱 {T("Crop work", "పంట పనులు")}</h4>'
          + f'<div class="today-lines">{lines(u["crop_lines"])}</div>')
        st.caption(T("Crop reminders are demo timings. Check with your AEO before using fertilizer or medicine.",
                     "పంట గుర్తుచేతలు డెమో సమయాలు మాత్రమే. ఎరువు లేదా మందు వాడే ముందు మీ AEO ని అడగండి."))
        c1, c2 = st.columns(2)
        if c1.button("🔊 " + T("Read aloud", "చదివి వినిపించండి"), width="stretch", key="today_speak"):
            speak_aloud(today.speech(u, lang), lang)
        if c2.button("✅ " + T("Done", "సరే"), type="primary", width="stretch", key="today_done"):
            page_js("window.rmQuiet && rmQuiet()")
            st.rerun()

    st.dialog("🌾 " + T("Today on your farm", "ఈరోజు మీ పొలంలో"), width="medium")(box)()


def bell(user):
    """🔔 Notification bell: questions about remedies Crop Doctor gave - did you use it, when, did it
    work, then a photo of the medicine used and of the crop now. Every answer is saved to My history."""
    waiting = [r for r in history.records(user["farmer_id"]) if not r["feedback"]][::-1]  # oldest first
    with st.popover("🔔" + (f" {len(waiting)}" if waiting else ""), width="content"):
        st.markdown("**🔔 " + T("Notifications", "నోటిఫికేషన్లు") + "**")
        if ss.get("bell_saved"):
            st.success(ss.pop("bell_saved"))
        if ss.get("bell_error"):
            st.error(ss.pop("bell_error"))
        if not waiting:
            st.caption(T("No new notifications.", "కొత్త నోటిఫికేషన్లు ఏవీ లేవు."))
        for rec in waiting:
            bell_item(user, rec)


def bell_item(user, rec):
    """One remedy: the questions one at a time, then (if it was used) photos of the medicine and the crop now."""
    te = is_te()
    state = ss.setdefault("bell", {}).setdefault(rec["id"], {"step": "used", "answers": {}})
    with st.container(border=True, key=f"bell_{rec['id']}"):
        st.markdown(fu_intro(rec, te).replace("\n", "  \n"))  # keep the line break
        if state["step"] != "photo":
            question, options = fu_step(state["step"], rec, te)
            st.markdown(f"**{question}**")
            with st.container(horizontal=True, gap="small", key=f"bellr_{rec['id']}"):
                for value, label in options:
                    # on_click (not st.rerun) keeps the bell open between questions
                    st.button(label, key=f"bellb_{rec['id']}_{state['step']}_{value}",
                              on_click=bell_answer, args=(user, rec, value))
            return
        pics = {}
        for kind, title, hint in (
                ("medicine", "💊 " + T("Send a picture of the medicine you used", "మీరు వాడిన మందు ఫోటో పంపండి"),
                 T("The bottle or packet, so we can see the name.", "మందు డబ్బా లేదా ప్యాకెట్ — పేరు కనిపించేలా.")),
                ("after", "📷 " + T("Send a photo of your crop now", "ఇప్పుడు మీ పంట ఫోటో పంపండి"),
                 T("We keep it next to the first photo, so you can see before and after.",
                   "మొదటి ఫోటో పక్కనే ఉంచుతాం — ముందు, తర్వాత చూడవచ్చు."))):
            st.markdown(f"**{title}**")
            st.caption(hint)
            up = st.file_uploader(title, type=["jpg", "jpeg", "png", "webp"], key=f"bellpic_{kind}_{rec['id']}",
                                  label_visibility="collapsed")
            if up:
                pics[kind] = up.getvalue()
        c1, c2 = st.columns(2)
        c1.button(T("Skip photos", "ఫోటోలు వద్దు"), key=f"bellskip_{rec['id']}", width="stretch",
                  on_click=bell_save, args=(user, rec, None))
        c2.button(T("Save", "సేవ్ చేయండి"), key=f"bellsave_{rec['id']}", type="primary", width="stretch", disabled=not pics,
                  on_click=bell_save, args=(user, rec, pics))


def bell_answer(user, rec, value):
    state = ss.bell[rec["id"]]
    state["answers"][FU_FIELD[state["step"]]] = value
    nxt = fu_next(state["step"], value, rec)
    if nxt:
        state["step"] = nxt
    elif state["answers"]["used"] == "no":
        bell_save(user, rec, None)
    else:
        state["step"] = "photo"  # used it: ask for photos of the medicine and the crop now


def bell_save(user, rec, photos):
    """photos: {"medicine": bytes, "after": bytes}, or None."""
    answers = ss.bell[rec["id"]]["answers"]
    try:
        history.save_feedback(rec["id"], user, answers)
        for kind, image in (photos or {}).items():
            history.save_photo(rec["id"], kind, image, user)
    except history.HistoryError as e:
        ss.bell_error = err(e)
        return
    ss.bell.pop(rec["id"], None)
    thanks = T("🙏 Thank you! Your answer is saved in 📜 My history. It helps other farmers too.",
               "🙏 ధన్యవాదాలు! మీ సమాధానం 📜 నా చరిత్ర లో సేవ్ అయింది. ఇది ఇతర రైతులకు కూడా సహాయపడుతుంది.")
    if answers.get("result") in ("no_change", "worse"):
        thanks += " " + T("Sorry it did not work. Please contact your AEO, or send a new photo in Crop Doctor.",
                          "ఫలితం బాగోలేదు. మీ AEO ని సంప్రదించండి లేదా పంట వైద్యుడు లో మళ్లీ ఫోటో పంపండి.")
    ss.bell_saved = thanks


def page_chat(user, embedded=False):
    """One chat for typing and talking. embedded = shown under the farmer's details on My Details."""
    # WhatsApp look is opened from the floating WhatsApp button
    channel = "WhatsApp" if ss.get("wa_mode") else "Web chatbot"
    lang = ss.ui_lang  # quick questions follow the తెలుగు | English switch
    clicked = None
    if embedded:
        provider, farmer_id = "claude", user["farmer_id"]
        main = st.container(key="farmer_chat")
        if ss.pop("wa_scroll", False):
            page_js("document.querySelector('.st-key-farmer_chat')?.scrollIntoView({behavior: 'smooth', block: 'start'})",
                    wait_for=".st-key-farmer_chat")
        chat_window(user, main, channel, lang, provider, farmer_id, clicked, quick=True)
        return
    side, main = st.columns([1, 2.6], gap="medium")
    with side, st.container(key="panel_settings"):
        st.markdown("### " + T("Settings", "సెట్టింగ్‌లు"))
        provider = seg(T("AI model", "AI మోడల్"), list(MODEL_CHOICES), "chat_model", MODEL_CHOICES)
        if user["role"] == "farmer":
            farmer_id = user["farmer_id"]
            st.text_input(T("Logged in as", "లాగిన్ అయిన రైతు ID"), farmer_id, disabled=True)
        else:
            ids = [""] + [f["farmer_id"] for f in data.FARMERS]
            farmer_id = st.selectbox("Farmer ID (staff can test any farmer)", ids,
                                     format_func=lambda i: i and f"{i} · {data.FARMER_INDEX[i]['name']}" or "— optional —")
        f = data.FARMER_INDEX.get(farmer_id or "")
        if f:
            district = f["district_te"] if is_te() else f["district"]
            H(f'<div class="farmer-chip">✅ {f["name"]}<br><small>{f["village"]}, {district} · '
              f'{f["total_acres"]} {T("acres", "ఎకరాలు")} · {", ".join(crop_name(c) for c in f["crops"])}</small></div>')
        st.markdown("**" + T("Try asking", "ఇలా అడగండి") + "**")
        with st.container(key="quick", gap="small"):
            for q in QUICK[lang]:
                if st.button(q, key=f"q_{q}", width="stretch"):
                    clicked = q
        if st.button("🗑️ " + T("Clear chat", "చాట్ తుడిచేయండి"), type="tertiary"):
            ss.chat = []
            st.rerun()
    chat_window(user, main, channel, lang, provider, farmer_id, clicked)


def follow_new_messages():
    """Keep the chat scrolled to the newest message: whenever the messages grow (a question,
    an answer, a photo), scroll the chat box to the bottom. Scrolling up to read stays put."""
    page_js("""
if (!window.rmFollowChat) {
  window.rmFollowChat = setInterval(() => {
    document.querySelectorAll('.st-key-msgs').forEach((b) => {
      if (b.scrollHeight !== Number(b.dataset.seenHeight)) {
        b.dataset.seenHeight = b.scrollHeight;
        b.scrollTo({ top: b.scrollHeight, behavior: 'smooth' });
      }
    });
  }, 300);
}""")


def chat_window(user, main, channel, lang, provider, farmer_id, clicked, quick=False):
    """quick: the suggested questions sit inside the chat, under the welcome message."""
    with main, st.container(key="phone_wa" if channel == "WhatsApp" else "phone"):
        sub = (T("Telangana Agriculture Dept · Verified business", "తెలంగాణ వ్యవసాయ శాఖ · ధృవీకరించిన ఖాతా")
               if channel == "WhatsApp" else T("Type or tap the mic to talk", "టైప్ చేయండి లేదా మైక్ నొక్కి మాట్లాడండి"))
        # The farmer's chat on Home says "Ask Rythu Mitra" right in its green header
        title = T("Ask Rythu Mitra", "రైతు మిత్రను అడగండి") if quick else T("Rythu Mitra", "రైతు మిత్ర")
        H(f'<div class="phone-head"><div class="avatar">🌾</div><div><b>{title}</b>'
          f'<small>{sub}</small></div></div>')
        ss.setdefault("chat", [])
        te = lang == "te"
        relang_chat(lang)
        box = st.container(height=480, key="msgs", border=False)
        follow_new_messages()
        with box:
            H(f'<div class="msg bot">{rich(WELCOME[lang])}</div>')
            if quick:  # tap a suggestion to ask it
                with st.container(horizontal=True, gap="small", key="quick_row"):
                    for q in QUICK[lang]:
                        if st.button(q, key=f"q_{q}"):
                            clicked = q
            for m in ss.chat:
                show_message(m)
        sent = st.chat_input("మీ ప్రశ్న టైప్ చేయండి లేదా మైక్ నొక్కండి... 📎 ఫోటో కూడా పంపవచ్చు" if lang == "te"
                             else "Type your question or tap the mic... 📎 or send a crop photo",
                             accept_file="multiple", file_type=MEDIA_TYPES, key="chat_box")
        mic_button(lang)
        recorded = None
        if channel == "WhatsApp":
            # WhatsApp also takes a recorded voice message
            with st.container(key="voice_pad"):
                ss.setdefault("rec_n", 0)
                recorded = st.audio_input(T("🎙️ Record a voice message, then it is sent", "🎙️ వాయిస్ మెసేజ్ రికార్డ్ చేయండి — ఆపగానే పంపబడుతుంది"),
                                          key=f"rec_{ss.rec_n}")
        if ss.get("speak_next") and channel != "WhatsApp":
            speak_aloud(ss.pop("speak_next"), lang)  # a spoken question gets a spoken answer
        ss.pop("speak_next", None)
        question = (sent if isinstance(sent, str) else (sent.text if sent else "")) or clicked
        if recorded:
            ss.rec_n += 1  # a fresh recorder for the next message
            text = ai.transcribe(recorded.getvalue(), "voice.wav", lang)
            audio = f"data:audio/wav;base64,{base64.b64encode(recorded.getvalue()).decode()}"
            if not text:
                # Mock mode: nothing can turn a recording into words without an AI key
                ss.chat.append({"role": "user", "audio": audio, "text": ""})
                ss.chat.append({"role": "bot", "followup": True, "tx": {
                    "en": "🎙️ I got your voice message. In this demo (Mock AI mode) a recording can't be turned into words — "
                          "that needs an AI key. Please tap the **mic** in the chat box and speak, or type your question.",
                    "te": "🎙️ మీ వాయిస్ మెసేజ్ అందింది. ఈ డెమో (మాక్ AI మోడ్)లో రికార్డింగ్‌ను మాటలుగా మార్చలేము — దానికి AI కీ కావాలి. "
                          "దయచేసి చాట్ బాక్స్‌లో **మైక్** నొక్కి మాట్లాడండి, లేదా ప్రశ్న టైప్ చేయండి."}})
                st.rerun()
            question, ss.voice_audio = VOICE_MARK + text, audio
        photos = [] if not sent or isinstance(sent, str) else list(sent.files or [])
        if photos:
            chat_photo(user, photos, lang, provider, box)
            st.rerun()
        voice = bool(question and question.startswith(VOICE_MARK))  # spoken with the mic button
        question = question.removeprefix(VOICE_MARK) if question else question
        if question:
            ss.chat.append({"role": "user", "text": question, "voice": voice and channel == "WhatsApp",
                            "audio": ss.pop("voice_audio", None)})
            with box:
                show_message(ss.chat[-1])
                with st.spinner(T("Typing...", "టైప్ చేస్తోంది...")):
                    gathered = assistant.gather(question, farmer_id or None, **gather_lang(lang))
                    res = ai.answer(ai.pick(provider), question, gathered)
            log_query(gathered["intent"], gathered["lang"], provider, channel, farmer_id)
            ss.chat.append({"role": "bot", **res, "stage": gathered["stage"], "sources": gathered["sources"],
                            "voice": voice and channel == "WhatsApp", "lang": gathered["lang"],
                            "ask": {"question": question, "farmer_id": farmer_id or None, "provider": provider}})
            if voice:
                ss.speak_next = res["text"]
            st.rerun()


def relang_chat(lang):
    """Language switched: redo earlier answers in the new language (not counted again on the dashboard)."""
    for m in ss.chat:
        if m.get("ask") and m.get("lang") != lang:
            a = m["ask"]
            gathered = assistant.gather(a["question"], a["farmer_id"], **gather_lang(lang))
            m.update(ai.answer(ai.pick(a["provider"]), a["question"], gathered), stage=gathered["stage"],
                     sources=gathered["sources"], lang=lang)


def gather_lang(lang):
    """Ask for replies in the switch's language, if this backend version supports it."""
    return {"lang": lang} if "lang" in inspect.signature(assistant.gather).parameters else {}


VOICE_MARK = "\u2063"  # invisible mark the mic button puts in front of a spoken question


VOICE_HELLO = {"en": "Welcome to Rythu Mitra. You can now talk and ask your question.",
               "te": "రైతు మిత్రకు స్వాగతం. ఇప్పుడు మీరు మాట్లాడి మీ ప్రశ్న అడగవచ్చు."}
VOICE_AGAIN = {"en": "Please ask your question.", "te": "మీ ప్రశ్న అడగండి."}


def audio_url(text):
    """Telugu audio for a short fixed sentence, if Gemini has made it already (it is made in the
    background the first time, so the page never waits)."""
    audio = ai.speak_later(text, "te")
    return "data:audio/wav;base64," + base64.b64encode(audio).decode() if audio else ""


def mic_button(lang):
    """A mic button inside the chat box: it says the welcome aloud in the chosen language, then the
    browser listens (Chrome/Edge), fills the box and sends it. The answer is read back aloud."""
    page_js(wait_for='[data-testid="stChatInput"] textarea', code=f"""
(() => {{
  const box = document.querySelector('[data-testid="stChatInput"]');
  if (!box) return;
  let b = box.querySelector('.mic-btn');
  if (!b) {{
    b = document.createElement('button'); b.className = 'mic-btn'; b.type = 'button'; b.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2z"/></svg>';
    box.appendChild(b);
    b.onclick = () => {{
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR) {{ alert(b.dataset.lang === 'te' ? 'మాట్లాడి అడగడానికి Chrome లేదా Edge కావాలి.' : 'Voice input needs Chrome or Edge.'); return; }}
      const te = b.dataset.lang === 'te';
      const listen = () => {{
        const rec = new SR(); rec.lang = te ? 'te-IN' : 'en-IN';
        b.classList.remove('talk'); b.classList.add('rec');
        rec.onresult = (e) => {{
          const ta = box.querySelector('textarea');
          Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(ta, '{VOICE_MARK}' + e.results[0][0].transcript);
          ta.dispatchEvent(new Event('input', {{bubbles: true}}));
          setTimeout(() => box.querySelector('[data-testid="stChatInputSubmitButton"]')?.click(), 150);
        }};
        rec.onend = () => b.classList.remove('rec');
        rec.start();
      }};
      // Welcome aloud first (the full welcome once, then a short prompt), then listen
      const again = !!window.rmGreeted;
      const hello = again ? JSON.parse(b.dataset.again) : JSON.parse(b.dataset.hello);
      window.rmGreeted = true;
      b.classList.add('talk');
      rmSay(hello[te ? 'te' : 'en'], te ? 'te' : 'en', (again ? b.dataset.againUrl : b.dataset.helloUrl) || '', listen);
    }};
  }}
  b.dataset.lang = '{lang}';
  b.dataset.helloUrl = '{audio_url(VOICE_HELLO["te"]) if lang == "te" else ""}';  // Gemini Telugu voice, when ready
  b.dataset.againUrl = '{audio_url(VOICE_AGAIN["te"]) if lang == "te" else ""}';
  b.dataset.hello = {json.dumps(json.dumps(VOICE_HELLO, ensure_ascii=False))};
  b.dataset.again = {json.dumps(json.dumps(VOICE_AGAIN, ensure_ascii=False))};
  b.title = '{"మాట్లాడండి" if lang == "te" else "Speak"}';
}})();
""")


def speak_aloud(text, lang):
    """Read text aloud with a real voice for the language. Chrome on Windows has no Telugu voice and
    reads Telugu letters with an English voice, which sounds wrong - so Telugu is spoken by Gemini
    (when its key is set); otherwise the browser's own Telugu voice if it has one (Edge does)."""
    clean = re.sub(r"\*\*|[•💡➡️📄⚠️]", "", text)
    audio = None
    if lang == "te":
        with st.spinner("గొంతు సిద్ధమవుతోంది…"):
            audio = ai.speak(clean, lang)
    url = "data:audio/wav;base64," + base64.b64encode(audio).decode() if audio else ""
    page_js(SAY_JS + f"rmSay({json.dumps(clean)}, '{lang}', '{url}');")


# rmSay(text, lang, audioUrl, onEnd) / rmQuiet(): read aloud in the app page (see speak_aloud)
SAY_JS = """
window.rmQuiet = () => { window.speechSynthesis && speechSynthesis.cancel(); if (window.rmAudio) { window.rmAudio.onended = null; window.rmAudio.pause(); window.rmAudio = null; } };
window.rmSay = (text, lang, url, onEnd) => {
  rmQuiet();
  const done = () => onEnd && onEnd();
  if (url) { const a = new Audio(url); window.rmAudio = a; a.onended = a.onerror = done; a.play().catch(done); return; }
  const voices = window.speechSynthesis ? speechSynthesis.getVoices() : [];
  const own = voices.find((v) => (v.lang || '').toLowerCase().startsWith(lang === 'te' ? 'te' : 'en-in'));
  if (!window.speechSynthesis || (lang === 'te' && !own)) return done();  // no Telugu voice: say nothing rather than garble it
  const u = new SpeechSynthesisUtterance(text); u.lang = lang === 'te' ? 'te-IN' : 'en-IN'; if (own) u.voice = own;
  u.onend = u.onerror = done; window.rmUtterance = u; speechSynthesis.speak(u);
};
"""


MEDIA_TYPES = ["jpg", "jpeg", "png", "webp", "mp4", "mov", "webm", "mkv", "3gp", "m4v"]


def check_media(files, provider, lang, crop=None):
    """Any number of photos and videos of the same crop -> (diagnosis result, pictures).
    Videos become a few still frames; everything is checked together. Raises media.MediaError."""
    pics, _ = media.pictures([(f.getvalue(), f.type, f.name) for f in files])
    return ai.diagnose_many(ai.pick(provider), media.for_ai(pics), lang, crop), pics


def media_thumbs(files):
    """Small previews for the chat: each photo, and the first frame of each video (marked 🎬)."""
    out = []
    for f in files:
        if media.is_video(f.type, f.name):
            first = media.video_frames(f.getvalue(), f.name, count=1)[0]
            out.append({"url": "data:image/jpeg;base64," + base64.b64encode(first).decode(), "video": True})
        else:
            out.append({"url": f"data:{f.type or 'image/jpeg'};base64,{base64.b64encode(f.getvalue()).decode()}",
                        "video": False})
    return out


def chat_photo(user, files, lang, provider, box):
    """Crop photos / videos sent in the chat: diagnose them together, reply, save to History."""
    te = lang == "te"
    n_vid = sum(media.is_video(f.type, f.name) for f in files)
    n_pic = len(files) - n_vid
    with box, st.spinner(T("Looking at the photos...", "ఫోటోలు పరిశీలిస్తున్నాము...")):
        try:
            res, pics = check_media(files, provider, lang)
        except media.MediaError as e:
            ss.chat.append({"role": "bot", "followup": True, "tx": both(lambda t: f"⚠️ {terms.te_error(str(e)) if t else e}")})
            return
    ss.chat.append({"role": "user", "media": media_thumbs(files), "tx": {
        "te": f"తెగులు సోకిన పంట — {n_pic} {'ఫోటో' if n_pic == 1 else 'ఫోటోలు'}"
              + (f", {n_vid} {'వీడియో' if n_vid == 1 else 'వీడియోలు'}" if n_vid else ""),
        "en": f"Affected crop — {n_pic} photo{'s' if n_pic != 1 else ''}" + (f", {n_vid} video{'s' if n_vid != 1 else ''}" if n_vid else "")}})
    found = res["diagnosis"]
    saved = (found["status"] == "detected" and user["role"] == "farmer"
             and history.add(user["farmer_id"], found["disease_id"], found["confidence"], None, "Chat photo",
                             photo=pics[0][0]))

    def reply(te):  # built for both languages, so it follows the language switch
        d = ai.diagnosis_in(found, "te" if te else "en")
        if d["status"] != "detected":
            return f"**{d['name']}** — {d['remedy']}"
        text = (f"**గుర్తింపు: {d['name']}** ({d['crop']}) — నమ్మకం {round(d['confidence'] * 100)}%\n\nలక్షణాలు: {d['symptoms']}\n\n"
                f"నివారణ: {d['remedy']}\n\n📋 పూర్తి మందుల ప్రణాళిక కోసం **పంట వైద్యుడు** ట్యాబ్ చూడండి.\n⚠️ మందులు వాడే ముందు మీ AEO ని సంప్రదించండి."
                if te else
                f"**Detected: {d['name']}** ({d['crop']}) — {round(d['confidence'] * 100)}% confidence\n\nSymptoms: {d['symptoms']}\n\n"
                f"Remedy: {d['remedy']}\n\n📋 Open the **Crop Doctor** tab for the full spray plan.\n⚠️ Please confirm with your AEO before spraying.")
        if saved:
            text += ("\n📜 మీ చరిత్రలో సేవ్ అయింది. మందు వాడిన తర్వాత పైన 🔔 గంటలో ఫలితం, ఫోటో పంపండి." if te
                     else "\n📜 Saved to your History. After you use the remedy, tell us the result and send a photo from the 🔔 bell at the top.")
        return text
    ss.chat.append({"role": "bot", "followup": True, "tx": both(reply)})
    ss.speak_next = reply(te)


def voice_note(text):
    """WhatsApp-style voice note: play button, sound bars and length (about 2.5 words a second)."""
    secs = max(2, round(len(text.split()) / 2.5))
    bars = "".join(f'<i style="height:{4 + (i * 7 + secs * 3) % 13}px"></i>' for i in range(22))
    return (f'<div class="voice-note"><span class="play">▶</span><span class="bars">{bars}</span>'
            f'<small>{secs // 60}:{secs % 60:02d}</small></div>')


def show_message(m):
    if m["role"] == "user":
        img = f'<img src="{m["image"]}" class="thumb">' if m.get("image") else ""
        if m.get("media"):
            img += '<div class="msg-media">' + "".join(
                f'<div class="mm"><img src="{x["url"]}">{"<span>🎬</span>" if x["video"] else ""}</div>' for x in m["media"]) + "</div>"
        if m.get("audio"):
            img += f'<audio controls src="{m["audio"]}" class="vm-audio"></audio>'
        if m.get("audio") and not m.get("voice"):
            H(f'<div class="msg user">{img}{rich(msg_text(m))}</div>')
            return
        if m.get("voice"):
            player = f'<audio controls src="{m["audio"]}" class="vm-audio"></audio>' if m.get("audio") else voice_note(msg_text(m))
            H(f'<div class="msg user">{player}<div class="transcript">{rich(msg_text(m))}</div></div>')
        else:
            H(f'<div class="msg user">{img}{rich(msg_text(m))}</div>')
        return
    if m.get("followup"):
        H(f'<div class="msg bot fu">{rich(msg_text(m))}</div>')
        return
    stage = STAGE_TE.get(m["stage"], m["stage"]) if is_te() else m["stage"]
    model = m["model"].replace("(mock)", "(మాక్)") if is_te() else m["model"]
    tags = (f'<span class="tag stage">{html.escape(stage)}</span>'
            + "".join(f'<span class="tag">{html.escape(source_label(s))}</span>' for s in m["sources"])
            + f'<span class="tag model">{model} · {m["latency_ms"]} ms · {m["tokens_out"]} {T("tokens", "టోకెన్లు")}</span>')
    note = m.get("note") or ""
    if note.startswith("Live call failed") and is_te():
        note = "లైవ్ AI పనిచేయలేదు; మాక్ సమాధానం చూపిస్తున్నాం."
    note = f'<div class="note">{html.escape(note)}</div>' if note else ""
    vn = voice_note(msg_text(m)) if m.get("voice") else ""
    H(f'<div class="msg bot">{vn}{rich(msg_text(m))}<div class="meta">{tags}</div>{note}</div>')


# ---------------------------------------------------------------------------
# Crop Doctor
# ---------------------------------------------------------------------------

# Telugu for how to apply each remedy (diseases.py has Telugu for why / when / repeat only).
# Medicine names show in Telugu with the English bottle label in brackets (terms.medicine).
METHOD_TE = {
    "Apply a pinch into each whorl": "ప్రతి సుడిలో చిటికెడు వేయండి",
    "Broadcast granules in standing water": "నిలువ నీటిలో గుళికలు చల్లండి",
    "Foliar spray": "ఆకులపై పిచికారీ",
    "Hang just above crop canopy": "పంట పైభాగానికి కొంచెం పైన వేలాడదీయండి",
    "Install traps above crop height": "పంట ఎత్తు కంటే పైన బుట్టలు పెట్టండి",
    "Install traps at crop height": "పంట ఎత్తులో బుట్టలు పెట్టండి",
    "Mix with manure and apply to soil": "పశువుల ఎరువుతో కలిపి నేలలో వేయండి",
    "Soil drench around the plant base": "మొక్క మొదలు చుట్టూ నేలలో పోయండి",
    "Spray covering the underside of leaves": "ఆకుల అడుగు భాగం తడిసేలా పిచికారీ చేయండి",
    "Spray directed at the base of plants": "మొక్కల మొదళ్లకు తగిలేలా పిచికారీ చేయండి",
    "Spray directed into the whorl": "సుడిలోకి పడేలా పిచికారీ చేయండి",
}


def tr(t, field):
    """One line of spray guidance (reason / when / repeat / method) in the chosen language."""
    if not is_te():
        return t[field]
    return t.get(field + "_te") or METHOD_TE.get(t[field], t[field])


def dose_te(text):
    """'2 ml per litre · 32 ml per 16-L tank · 12.5 tanks' -> Telugu word order."""
    if not is_te():
        return text
    text = re.sub(r"([\d.]+ \w+) per litre", r"లీటరుకు \1", text)
    text = re.sub(r"([\d.]+ \w+) per (\d+)-L tank", r"\2 లీటర్ల ట్యాంకుకు \1", text)
    text = re.sub(r"([\d.]+ \w+) per acre", r"ఎకరానికి \1", text)
    return re.sub(r"([\d.]+) tanks", r"\1 ట్యాంకులు", text)


def page_doctor(user):
    lang = ss.ui_lang  # the report follows the తెలుగు | English switch
    top_l, top_r = st.columns([1.3, 1], gap="medium")
    with top_r, st.container(key="panel_doc_settings"):
        st.markdown("### " + T("Your field", "మీ పొలం"))
        crop = st.selectbox(T("Crop (optional)", "పంట (తప్పనిసరి కాదు)"), [""] + list(data.CROPS),
                            format_func=lambda c: crop_name(c) if c else T("Not sure", "తెలియదు"))
        acres = st.number_input(T("Field size (acres)", "పొలం విస్తీర్ణం (ఎకరాలు)"), 0.1, 100.0, 1.0, 0.5)
        provider = seg(T("AI model", "AI మోడల్"), list(MODEL_CHOICES), "doctor_model", MODEL_CHOICES)
    with top_l, st.container(key="panel_photo"):
        st.markdown("## 🩺 " + T("Crop Doctor", "పంట వైద్యుడు"))
        H('<p class="muted">' + T("Upload photos or videos of the affected plant. You get the problem, why it happens, and exactly "
                                  "how much to spray for your field.",
                                  "తెగులు సోకిన మొక్క ఫోటోలు లేదా వీడియోలు పెట్టండి. సమస్య ఏమిటి, ఎందుకు వచ్చింది, మీ పొలానికి ఎంత మందు "
                                  "కొట్టాలో చెబుతాము.") + "</p>")
        ups = st.file_uploader(T("Crop photos and videos", "పంట ఫోటోలు, వీడియోలు"), type=MEDIA_TYPES,
                               accept_multiple_files=True, label_visibility="collapsed", key="crop_photo")
        st.caption(T("Add as many photos and videos as you like · photos up to 8 MB, videos up to 50 MB",
                     "ఎన్ని ఫోటోలు, వీడియోలు అయినా జోడించవచ్చు · ఫోటో 8 MB, వీడియో 50 MB వరకు"))
        if ups:
            with st.container(horizontal=True, gap="small", key="doc_thumbs"):
                for f in ups:
                    if media.is_video(f.type, f.name):
                        st.video(f, width=180)
                    else:
                        st.image(f, width=110)
            label = T(f"🔍 Analyse {len(ups)} photo{'s' if len(ups) != 1 else ''} / video{'s' if len(ups) != 1 else ''}",
                      f"🔍 {len(ups)} ఫోటోలు / వీడియోలు పరిశీలించండి")
            if st.button(label, type="primary", width="stretch"):
                with st.spinner(T("Looking at the leaves...", "ఆకులను పరిశీలిస్తున్నాం...")):
                    try:
                        res, pics = check_media(ups, provider, lang, crop or None)
                    except media.MediaError as e:
                        st.error(err(e))
                        res = None
                if res:
                    log_query("pest_diagnosis", lang, provider)
                    ss.diagnosis = res
                    # Farmers: save it (with the first picture) to History; the 🔔 bell asks later if the remedy worked
                    d = res["diagnosis"]
                    ss.diag_saved = bool(user["role"] == "farmer" and d["status"] == "detected" and history.add(
                        user["farmer_id"], d["disease_id"], d["confidence"], acres, "Crop Doctor", photo=pics[0][0]))

    res = ss.get("diagnosis")
    if res:
        d = res["diagnosis"]
        if ss.get("diag_saved"):
            c1, c2 = st.columns([4, 1], vertical_alignment="center")
            c1.markdown('<div class="saved-note">' + T(
                "📜 Saved to your History. After you use the remedy, tell us the result and send a photo from the 🔔 bell at the top.",
                "📜 మీ చరిత్రలో సేవ్ అయింది. మందు వాడిన తర్వాత పైన 🔔 గంటలో ఫలితం, ఫోటో పంపండి.") + "</div>",
                unsafe_allow_html=True)
            if c2.button("📜 " + T("Open History", "చరిత్ర తెరవండి"), width="stretch"):
                ss.view = "history"
                st.rerun()
        with st.container(key="panel_result"):
            if res["mode"] == "mock":
                H('<div class="demo-otp">' + T(
                    "Mock AI mode: the photo is not really analysed — a matching problem is picked "
                    "from the library. Add an API key to use real Claude / ChatGPT vision.",
                    "మాక్ AI మోడ్: ఫోటోను నిజంగా పరిశీలించలేదు — సమాచారం నుండి ఒక సమస్యను ఎంచుకున్నాము. "
                    "నిజమైన Claude / ChatGPT కోసం API కీ పెట్టండి.") + "</div>")
            if d["status"] != "detected":
                # Worded again in the language that is on now (the result may be from before a switch)
                d = ai._diagnosis("healthy" if d["status"] == "healthy" else None, d["confidence"], d.get("observed"), lang)
                st.warning(f"**{d['name']}** — {d['remedy']}")
            else:
                report(diseases.INDEX[d["disease_id"]], acres, lang, confidence=d["confidence"])

    with st.container(key="panel_library"):
        st.markdown("### 📚 " + T("Disease library", "తెగుళ్ల సమాచారం"))
        crops = sorted({d["crop"] for d in diseases.DISEASES})
        # Crop buttons, and a small search beside them for any crop or problem name (English or Telugu)
        with st.container(horizontal=True, vertical_alignment="bottom", gap="small", key="lib_crop_row"):
            pick_crop = (st.pills(T("Crop", "పంట"), crops, default=crops[0], key="lib_crop", format_func=crop_name)
                         or crops[0])
            query = st.text_input(T("Search", "వెతకండి"), key="lib_q", label_visibility="collapsed", width=230,
                                  placeholder="🔍 " + T("Search crop or problem", "పంట / సమస్య వెతకండి")).strip()
        label = lambda d: f"{d['name_te']} ({V(d['type'])})" if is_te() else f"{d['name']} ({d['type']})"
        if query:
            found, crop = diseases.search(query)
            if not found:
                name = crop_name(crop) if crop else query
                st.info(T(f"No problems for **{name}** in this demo library yet. Send a photo of the plant to Crop Doctor "
                          "above, or ask your AEO.",
                          f"**{name}** కు ఈ డెమో సమాచారంలో ఇంకా తెగుళ్లు లేవు. పైన పంట వైద్యుడికి మొక్క ఫోటో పంపండి, "
                          "లేదా మీ AEO ని అడగండి."))
                return
            dz = st.selectbox(T(f"Problem · {len(found)} found", f"సమస్య · {len(found)} దొరికాయి"), found, key="lib_dz_q",
                              format_func=lambda d: f"{crop_name(d['crop'])} · {label(d)}")
        else:
            options = [d for d in diseases.DISEASES if d["crop"] == pick_crop]
            dz = st.selectbox(T("Problem", "సమస్య"), options, key="lib_dz", format_func=label)
        report(dz, acres, lang)


def report(d, acres, lang, confidence=None):
    te = lang == "te"
    tank = diseases.SPRAYER_TANK_L
    conf = (f'<span class="pill soft">{round(confidence * 100)}% {"నమ్మకం" if te else "confidence"}</span>'
            if confidence else "")
    H(f"""<div class="dz-head"><div><div class="dz-name">{d['name_te'] if te else d['name']}</div>
<span class="muted">{data.CROPS[d['crop']] if te else d['crop']} · {terms.te(d['type']) if te else d['type']}</span></div>{conf}</div>
<div class="grid2"><div class="box"><b>{'ఎందుకు వస్తుంది' if te else 'Why it happens'}</b>{d['cause_te'] if te else d['cause']}</div>
<div class="box"><b>{'లక్షణాలు' if te else 'Symptoms to check'}</b>{d['symptoms_te'] if te else d['symptoms']}</div></div>""")
    cards = []
    for i, t in enumerate(diseases.plan_for(d, acres)):
        icon = "🧪" if t["kind"] == "Chemical" else "🌿"
        if t["per"] == "litre":
            qty = (f'<div><small>{T("Per litre", "లీటరుకు")}</small><b>{fmt(t["dose"], t["unit"])}</b></div>'
                   f'<div><small>{T(f"Per {tank} L tank", f"{tank} లీటర్ల ట్యాంకుకు")}</small><b>{fmt(t["per_tank"], t["unit"])}</b></div>'
                   f'<div><small>{T("Tanks · water", "ట్యాంకులు · నీరు")}</small><b>{t["tanks"]:g} · {t["water_total_l"]:g} L</b></div>'
                   f'<div class="total"><small>{T("Total to buy", "మొత్తం కొనాల్సింది")}</small><b>{fmt(t["total"], t["unit"])}</b></div>')
        else:
            qty = (f'<div><small>{T("Per acre", "ఎకరానికి")}</small><b>{fmt(t["dose"], t["unit"])}</b></div>'
                   f'<div class="total"><small>{T("Total to buy", "మొత్తం కొనాల్సింది")}</small><b>{fmt(t["total"], t["unit"])}</b></div>')
        phi = ""
        if t["phi_days"]:
            phi = '<div class="phi">' + T(f"Stop spraying {t['phi_days']} days before harvest.",
                                          f"కోతకు {t['phi_days']} రోజుల ముందు పిచికారీ ఆపండి.") + "</div>"
        best = T(" · Recommended", " · సిఫార్సు") if i == 0 else ""
        cards.append(f"""<div class="treat {'best' if i == 0 else ''}">
<div class="t-name">{icon} {terms.medicine(t['product'], is_te())}</div><span class="pill {'soft' if t['kind'] == 'Organic' else 'grey'}">{V(t['kind'])}{best}</span>
<div class="qty">{qty}</div>
<div><b>{T("Why:", "ఎందుకు:")}</b> {tr(t, 'reason')}</div><div><b>{T("When:", "ఎప్పుడు:")}</b> {tr(t, 'when')}</div>
<div><b>{T("Repeat:", "మళ్లీ:")}</b> {tr(t, 'repeat')}</div>
<div><b>{T("How:", "ఎలా:")}</b> {tr(t, 'method')}</div>{phi}</div>""")
    H(f"<h3>{'మందుల ప్రణాళిక' if te else 'Treatment plan'} — {acres:g} {'ఎకరాలు' if te else 'acres'}</h3>"
      f'<div class="treat-grid">{"".join(cards)}</div>')
    prev = "".join(f"<li>{p}</li>" for p in d["prevention_te" if te else "prevention"])
    safety = "".join(f"<li>{p}</li>" for p in diseases.SAFETY["te" if te else "en"])
    note = T("Doses come only from the vetted library — the AI never writes doses. Demo values; confirm with your AEO before spraying.",
             "మోతాదులు పరిశీలించిన సమాచారం నుండి మాత్రమే వస్తాయి — AI ఎప్పుడూ మోతాదు రాయదు. ఇవి డెమో విలువలు; "
             "పిచికారీ ముందు మీ AEO తో నిర్ధారించుకోండి.")
    H(f"""<div class="grid2"><div class="box"><b>{'నివారణ' if te else 'Prevention'}</b><ul>{prev}</ul></div>
<div class="box"><b>{'భద్రత' if te else 'Spraying safety'}</b><ul>{safety}</ul></div></div>
<p class="muted">{note}</p>""")


# ---------------------------------------------------------------------------
# Farmer Services / My Details (Stages 3-4)
# ---------------------------------------------------------------------------

WATER_ICON = {"Borewell": "🚰", "Canal": "🌊", "Tank": "💧", "Rainfed": "🌧️", "Drip": "💧", "Sprinkler": "💦"}


def farm_profile(f, farmer_view, home=False, back=False):
    """Profile header, land/crop summary and plot cards, with an Edit button.
    home: just the Namaskaram card (farmers edit under 👤 My details). back: a Back button."""
    e = html.escape
    with st.container(key="farmhero"):
        left, right = st.columns([2.6, 1.6], vertical_alignment="center")
        greeting = (T("Namaskaram", "నమస్కారం") + f", {e(f['name'].split()[0])} 🙏") if farmer_view else e(f["name"])
        place = f["district_te"] if is_te() else f["district"]
        # Signed up without a department Farmer ID: the AEO still has to check the details
        unverified = ('<span class="unverified">⏳ ' + T("Not yet verified by AEO", "AEO పరిశీలన పెండింగ్‌లో ఉంది") + "</span>"
                      if f.get("verified") is False else "")
        left.markdown(f"""<div class="farm-who"><div class="farm-avatar">{e(f["name"][0])}</div><div>
<div class="farm-name">{greeting}</div>
<div class="farm-sub">{f["farmer_id"]} · 📍 {e(f["village"])}, {place}
 · {T("Age", "వయస్సు")} {f["age"]} · {V(f["gender"])}{unverified}</div></div></div>""", unsafe_allow_html=True)
        # Edit and Back side by side on the right, away from the name
        with right, st.container(horizontal=True, horizontal_alignment="right", gap="small", key="hero_btns"):
            if not home and st.button("✏️ " + T("Edit details", "వివరాలు మార్చండి")):
                ss.editing = f["farmer_id"]
                ss.pop(f"plot_rows_{f['farmer_id']}", None)
                st.rerun()
            if back:
                st.button("← " + T("Back", "వెనక్కి"), key="details_back", on_click=go_home)
    if ss.get("profile_saved") == f["farmer_id"]:
        st.success(T("Saved to your account", "మీ ఖాతాలో సేవ్ అయింది") + " ✓")
        ss.pop("profile_saved")
    if home:
        return

    chips = "".join(f"<span>{data.crop_icon(c)} {crop_name(c)}</span>" for c in f["crops"])
    H(f"""<div class="farm-stats">
<div class="kpi"><small>{T("Total land", "మొత్తం భూమి")}</small><b>{f["total_acres"]:g} <span class="unit">{T("acres", "ఎకరాలు")}</span></b></div>
<div class="kpi"><small>{T("Land plots", "భూమి ముక్కలు")}</small><b>{len(f["plots"])}</b></div>
<div class="kpi"><small>{T("Crops", "పంటలు")}</small><b>{len(f["crops"])}</b><div class="crop-chips">{chips}</div></div>
<div class="kpi"><small>{T("Bank &amp; mobile", "బ్యాంక్ &amp; మొబైల్")}</small><b class="txt">{e(f["bank"])}</b><small>{T("Mobile", "మొబైల్")} {auth.mask(f["mobile"])}</small></div>
</div>""")

    with st.container(key="panel_land"):
        updated = ""
        if f.get("updated_on"):
            updated = (f'<span class="muted" style="float:right">{T("Last updated", "చివరిగా మార్చింది")} '
                       f'{day_label(datetime.fromisoformat(f["updated_on"]))} {f["updated_on"][:4]}, '
                       f'{time_label(datetime.fromisoformat(f["updated_on"]))}</span>')
        title = (T("My land &amp; crops", "నా భూమి &amp; పంటలు") if farmer_view else T("Land &amp; crops", "భూమి &amp; పంటలు"))
        H(f'<h3>🗺️ {title} <span class="tag stage">{T("Stage 4", "దశ 4")}</span>{updated}</h3>')
        cards = "".join(f"""<div class="plot-card"><div class="plot-crop">{data.crop_icon(p["crop"])}</div>
<div style="flex:1"><div class="plot-top"><b>{e(crop_name(p["crop"]))}</b><span class="pill soft">{p["area_acres"]:g} {T("ac", "ఎకరాలు")}</span></div>
<span class="muted">{T("Survey", "సర్వే నం.")} {e(p["survey_no"])} · {V(p.get("season", "Kharif"))}</span>
<div class="plot-meta"><span>🟫 {V(p["soil"])}</span><span>{WATER_ICON.get(p["irrigation"], "💧")} {V(p["irrigation"])}</span></div>
{crop_dates(p)}</div></div>"""
                        for p in f["plots"])
        H(f'<div class="plot-cards">{cards}</div>')


def crop_dates(p):
    """'Sown 10 Jun 2026 → harvest by 30 Nov 2026 · 33 days left' under a crop card."""
    if not p.get("sown_on") and not p.get("harvest_by"):
        return ('<div class="crop-dates muted">📅 ' + T("Add sowing and harvest dates in Edit details",
                                                      "విత్తిన / కోత తేదీలు వివరాలు మార్చండి లో జోడించండి") + "</div>")
    parts = []
    if p.get("sown_on"):
        d = date.fromisoformat(p["sown_on"])
        parts.append(f'<span>🌱 {T("Sown", "విత్తింది")} <b>{day_label(d)} {d.year}</b></span>')
    if p.get("harvest_by"):
        d = date.fromisoformat(p["harvest_by"])
        parts.append(f'<span>🧺 {T("Harvest by", "కోత")} <b>{day_label(d)} {d.year}</b></span>')
        left = (d - date.today()).days
        parts.append(f'<span class="pill green">{T(f"{left} days left", f"{left} రోజులు మిగిలాయి")}</span>' if left >= 0
                     else f'<span class="pill amber">{T("Harvest date passed", "కోత తేదీ దాటింది")}</span>')
    return f'<div class="crop-dates">{"".join(parts)}</div>'


def crop_label(name):
    """'🌾 Jowar (Sorghum) · జొన్న' — both names are in the label so typing either script finds the crop.
    In Telugu the Telugu name comes first."""
    te = data.crop_te(name)
    if te == name:
        return f"{data.crop_icon(name)} {name}"
    return f"{data.crop_icon(name)} {te} · {name}" if is_te() else f"{data.crop_icon(name)} {name} · {te}"


def farm_edit(f, farmer_view, setup=False):
    """Edit form for personal details and land plots; saves through profiles.update.
    setup: a farmer who just signed up fills an empty form (name and district come from the AEO record)."""
    o = profiles.options()
    fid = f["farmer_id"]
    rows_key = f"plot_rows_{fid}"
    if rows_key not in ss:  # one entry per plot; the number keeps widget keys stable when a plot is removed
        ss[rows_key] = [[0, {}]] if setup else [[i, dict(p)] for i, p in enumerate(f["plots"])]
        ss[rows_key + "_next"] = len(ss[rows_key])
    rows = ss[rows_key]
    crops = [c["name"] for c in o["crops"]]

    with st.container(key="panel_farmedit"):
        if setup:
            H('<div class="setup-head"><h2>🙏 ' + T("Welcome to Rythu Mitra!", "రైతు మిత్రకు స్వాగతం!") + "</h2><p>"
              + T("Before you start, please fill in your details, your land and your crops. We use them to give you the right advice.",
                  "మొదలుపెట్టే ముందు మీ వివరాలు, మీ భూమి, మీ పంటలు నింపండి. వీటితోనే మీకు సరైన సలహా ఇస్తాము.")
              + f'</p><small>{T("Farmer ID", "రైతు ID")} {fid}</small></div>')
        else:
            st.markdown("### ✏️ " + (T("Edit my details", "నా వివరాలు మార్చండి") if farmer_view
                                     else T("Edit farmer details", "రైతు వివరాలు మార్చండి")))
        st.markdown("**👤 " + T("Personal details", "వ్యక్తిగత వివరాలు") + "**")
        c = st.columns(3)
        name = c[0].text_input(T("Full name", "పూర్తి పేరు"), f["name"], key=f"ed_name_{fid}")
        village = c[1].text_input(T("Village", "గ్రామం"), "" if setup else f["village"], key=f"ed_village_{fid}")
        district = c[2].selectbox(T("District", "జిల్లా"), o["districts"], index=o["districts"].index(f["district"]),
                                  key=f"ed_district_{fid}", format_func=lambda d: data.DISTRICTS[d] if is_te() else d)
        c = st.columns(3)
        age = c[0].number_input(T("Age", "వయస్సు"), 18, 100, None if setup else int(f["age"]), key=f"ed_age_{fid}")
        gender = c[1].selectbox(T("Gender", "లింగం"), o["genders"], index=None if setup else o["genders"].index(f["gender"]),
                                key=f"ed_gender_{fid}", format_func=V, placeholder=T("Choose…", "ఎంచుకోండి…"))
        c[2].text_input(T("Mobile & bank", "మొబైల్ & బ్యాంక్"), f"{auth.mask(f['mobile'])} · {f['bank']}", disabled=True,
                        help=T("To change these, visit your AEO with proof.", "వీటిని మార్చాలంటే రుజువుతో మీ AEO ని కలవండి."))

        st.markdown(T("**🗺️ Land & crops** — in the Crop box, start typing (English or Telugu) to see suggestions. "
                      "A crop that is not in the list can be typed in too.",
                      "**🗺️ భూమి & పంటలు** — పంట పెట్టెలో పేరు టైప్ చేయడం మొదలుపెడితే (తెలుగు లేదా ఇంగ్లీష్) సూచనలు వస్తాయి. "
                      "జాబితాలో లేని పంటను కూడా టైప్ చేయవచ్చు."))
        plots = []
        for n, (rid, p) in enumerate(rows, 1):
            k = f"pl_{fid}_{rid}_"
            with st.container(key=f"plotrow_{fid}_{rid}"):
                c = st.columns([1.1, 0.9, 2.2, 1, 1.3, 1.2, 0.5], vertical_alignment="bottom")
                survey = c[0].text_input(T(f"Plot {n} · Survey no.", f"భూమి ముక్క {n} · సర్వే నం."), p.get("survey_no", ""),
                                         key=k + "survey", placeholder=T("e.g. 123/A", "ఉదా. 123/A"))
                area = c[1].number_input(T("Area (acres)", "విస్తీర్ణం (ఎకరాలు)"), 0.0, 100.0, float(p.get("area_acres") or 0),
                                         0.1, key=k + "area")
                options = crops if not p.get("crop") or p["crop"] in crops else [p["crop"]] + crops
                crop = c[2].selectbox(T("Crop", "పంట"), options, index=options.index(p["crop"]) if p.get("crop") else None,
                                      key=k + "crop", format_func=crop_label, accept_new_options=True,
                                      placeholder=T("Type a crop, e.g. jowar", "పంట పేరు టైప్ చేయండి, ఉదా. జొన్న"))
                season = c[3].selectbox(T("Season", "సీజన్"), o["seasons"], index=o["seasons"].index(p.get("season", "Kharif")),
                                        key=k + "season", format_func=V)
                # A new plot starts empty ("Choose…") so the farmer picks the soil and water source
                soil = c[4].selectbox(T("Soil", "నేల"), o["soils"], index=o["soils"].index(p["soil"]) if p.get("soil") else None,
                                      key=k + "soil", format_func=V, placeholder=T("Choose…", "ఎంచుకోండి…"))
                water = c[5].selectbox(T("Water source", "నీటి వనరు"), o["irrigation"],
                                       index=o["irrigation"].index(p["irrigation"]) if p.get("irrigation") else None,
                                       key=k + "water", format_func=V, placeholder=T("Choose…", "ఎంచుకోండి…"))
                if len(rows) > 1 and c[6].button("🗑", key=k + "remove", help=T("Remove this plot", "ఈ భూమి ముక్క తీసేయండి")):
                    ss[rows_key] = [r for r in rows if r[0] != rid]
                    st.rerun()
                # When this crop was sown and when the harvest is expected (both optional)
                c = st.columns([1.1, 1.1, 3.5])
                sown = c[0].date_input("🌱 " + T("Sown on", "విత్తిన తేదీ"),
                                       date.fromisoformat(p["sown_on"]) if p.get("sown_on") else None,
                                       key=k + "sown", format="DD/MM/YYYY")
                harvest = c[1].date_input("🧺 " + T("Harvest by", "కోత అంచనా తేదీ"),
                                          date.fromisoformat(p["harvest_by"]) if p.get("harvest_by") else None,
                                          key=k + "harvest", format="DD/MM/YYYY", min_value=sown)
            plots.append({"survey_no": survey, "area_acres": area, "crop": crop, "season": season,
                          "soil": soil, "irrigation": water,
                          "sown_on": sown.isoformat() if sown else None,
                          "harvest_by": harvest.isoformat() if harvest else None})

        if len(rows) < o["max_plots"] and st.button(T("＋ Add another plot", "＋ ఇంకో భూమి ముక్క జోడించండి"), width="stretch",
                                                    key=f"add_plot_{fid}"):
            ss[rows_key].append([ss[rows_key + "_next"], {}])
            ss[rows_key + "_next"] += 1
            st.rerun()
        total = sum(p['area_acres'] or 0 for p in plots)
        st.caption(T(f"Total: {total:g} acres", f"మొత్తం: {total:g} ఎకరాలు"))

        b1, b2, _ = st.columns([1.3, 1, 2.7])
        save_label = ("✅ " + T("Save and start", "సేవ్ చేసి మొదలుపెట్టండి")) if setup else ("💾 " + T("Save changes", "మార్పులు సేవ్ చేయండి"))
        if b1.button(save_label, type="primary", width="stretch", key=f"save_{fid}"):
            try:
                profiles.update(fid, {"name": name, "village": village, "district": district,
                                      "age": age, "gender": gender, "plots": plots})
                ss.pop("editing", None)
                ss.pop(rows_key, None)
                ss.profile_saved = fid
                st.rerun()
            except profiles.ProfileError as e:
                st.error(err(e))
        if not setup and b2.button(T("Cancel", "రద్దు చేయండి"), width="stretch", key=f"cancel_{fid}"):
            ss.pop("editing", None)
            ss.pop(rows_key, None)
            st.rerun()


def rupees(n):
    return f"₹{n:,}"


def payments(f):
    """Payment status: where the money of each scheme is right now."""
    e = html.escape
    bank = e(f["bank"])
    rows = []
    for a in (assistant._app_view(a) for a in f["applications"] if a["amount"]):
        s = a["status"]
        if s == "Credited":
            when = day_label(date.fromisoformat(a["credited_on"]))
            color, icon, note = "green", "✅", T(f"Credited on {when} to {bank}", f"{when} న {bank} ఖాతాలో జమ అయింది")
        elif s == "Approved":
            color, icon, note = "amber", "⏳", T("Approved — money will reach your bank soon", "ఆమోదం పొందింది — త్వరలో మీ ఖాతాలో జమ అవుతుంది")
        elif s.startswith("Rejected"):
            color, icon, note = "red", "❌", T("Not paid — application rejected. Raise a complaint under Grievances.",
                                               "చెల్లించలేదు — దరఖాస్తు తిరస్కరించబడింది. ఫిర్యాదులు లో ఫిర్యాదు చేయండి.")
        else:
            color, icon, note = "amber", "🔎", T("Not paid yet — application is being checked", "ఇంకా చెల్లించలేదు — దరఖాస్తు పరిశీలనలో ఉంది")
        scheme = a["scheme_te"] if is_te() else a["scheme"]
        rows.append(f'<div class="pay-row"><span class="pay-icon">{icon}</span>'
                    f'<span class="pay-main"><b>{e(scheme)}</b><small>{note}</small></span>'
                    f'<span class="pay-amt"><b>{rupees(a["amount"])}</b><span class="pill {color}">{e(V(s))}</span></span></div>')
    st.markdown(f'{T("Bank account", "బ్యాంకు ఖాతా")}: **{f["bank"]}**')
    if rows:
        st.markdown("".join(rows), unsafe_allow_html=True)
    else:
        st.write(T("No scheme payments for you yet.", "మీకు ఇంకా పథకం డబ్బు ఏదీ లేదు."))


def apply_scheme(fid):
    """➕ Apply for a scheme: pick one, see the benefit, who can apply and what to bring, then send.
    It starts as "Pending verification" and shows in the list above."""
    st.markdown("**➕ " + T("Apply for a scheme", "పథకానికి దరఖాస్తు చేయండి") + "**")
    done = ss.pop("applied", None)
    if done:
        st.success(T(f"Application for {done['scheme']} sent. ID {done['app_id']}. Status: {done['status']} — your AEO will check it.",
                     f"{done['scheme_te']} కు దరఖాస్తు పంపాం. ID {done['app_id']}. స్థితి: {V(done['status'])} — మీ AEO పరిశీలిస్తారు."),
                   icon="✅")
    open_ = applications.open_schemes(fid)
    if not open_:
        st.caption(T("You have applied for every scheme.", "అన్ని పథకాలకు మీరు దరఖాస్తు చేశారు."))
        return
    s = st.selectbox(T("Scheme", "పథకం"), open_, index=None, key=f"apply_pick_{fid}", label_visibility="collapsed",
                     format_func=lambda x: x["name_te"] if is_te() else x["name"],
                     placeholder=T("Choose a scheme…", "పథకం ఎంచుకోండి…"))
    if not s:
        return
    te = is_te()
    H(f'<div class="apply-info"><p><b>💰 {T("Benefit", "లాభం")}:</b> {html.escape(s["benefit_te" if te else "benefit"])}</p>'
      f'<p><b>✅ {T("Who can apply", "ఎవరు అర్హులు")}:</b> {html.escape(s["eligibility_te" if te else "eligibility"])}</p>'
      f'<p><b>📄 {T("What to keep ready", "సిద్ధంగా ఉంచుకోవాల్సినవి")}:</b> {html.escape(s["apply_te" if te else "apply"])}</p></div>')
    sure = st.checkbox(T("My land and bank details in My details are correct", "నా వివరాలు లో నా భూమి, బ్యాంక్ వివరాలు సరైనవి"),
                       key=f"apply_sure_{fid}")
    if st.button("📨 " + T("Send application", "దరఖాస్తు పంపండి"), type="primary", disabled=not sure, key=f"apply_go_{fid}"):
        try:
            ss.applied = assistant._app_view(applications.apply(fid, s["id"]))
            ss.pop(f"apply_pick_{fid}", None)
            ss.pop(f"apply_sure_{fid}", None)
            st.rerun()
        except applications.ApplicationError as e:
            st.error(err(e))


def side_sections(f, fid):
    """Applications, payments, grievances, weather and advisory: one row each (icon, name, a short
    hint and ›). Tapping a row opens what it contains."""
    e = html.escape
    pill = {"Credited": "green", "Approved": "green", "Resolved": "green", "Escalated": "red"}
    apps = [assistant._app_view(a) for a in f["applications"]]

    with st.expander(f"📋 {T('Scheme applications', 'పథకాల దరఖాస్తులు')}  ·  {len(apps)}",
                     expanded=bool(ss.get("applied"))):  # stays open to show the new application
        H("".join(
            f'<div class="side-row"><span class="grow"><b>{e(a["scheme_te"] if is_te() else a["scheme"])}</b>'
            f'<small class="muted">{a["app_id"]}</small></span><span class="pay-amt">'
            f'<span class="pill {pill.get(a["status"], "red" if a["status"].startswith("Rejected") else "amber")}">{e(V(a["status"]))}</span>'
            f'<small>{rupees(a["amount"]) if a["amount"] else "—"}</small></span></div>' for a in apps))

        apply_scheme(fid)

    credited = sum(a["amount"] for a in apps if a["status"] == "Credited")
    with st.expander(f"💰 {T('Payment status', 'డబ్బు జమ స్థితి')}  ·  {rupees(credited)}"):
        payments(f)

    mine = [g for g in data.GRIEVANCES if g["farmer_id"] == fid]
    still_open = sum(g["status"] != "Resolved" for g in mine)
    with st.expander(f"📣 {T('Grievances', 'ఫిర్యాదులు')}  ·  {still_open} {T('open', 'పెండింగ్')}"):
        if mine:
            H("".join(
                f'<div class="side-row"><span class="grow"><b>{g["grievance_id"]}</b> {e(V(g["category"]))}'
                f'<small class="muted">{day_label(date.fromisoformat(g["created_on"]))} · {e(V(g["channel"]))}</small></span>'
                f'<span class="pill {pill.get(g["status"], "amber")}">{e(V(g["status"]))}</span></div>' for g in mine))
        else:
            st.write(T("No grievances yet.", "ఇంకా ఫిర్యాదులు లేవు."))
        with st.form("griev", clear_on_submit=True, border=False):
            st.markdown("**" + T("Raise a new grievance", "కొత్త ఫిర్యాదు చేయండి") + "**")
            cat = st.selectbox(T("Category", "రకం"), data.GRIEVANCE_CATEGORIES, format_func=V)
            desc = st.text_area(T("Describe the problem", "సమస్య ఏమిటో రాయండి"))
            if st.form_submit_button(T("Submit grievance", "ఫిర్యాదు పంపండి"), type="primary"):
                if not desc.strip():
                    st.error(T("Please describe the problem.", "దయచేసి సమస్య ఏమిటో రాయండి."))
                else:
                    g = {"grievance_id": f"GRV-{2401 + len(data.GRIEVANCES)}", "farmer_id": fid,
                         "farmer_name": f["name"], "district": f["district"], "category": cat,
                         "description": desc.strip(), "status": "Open",
                         "created_on": date.today().isoformat(), "channel": "Web chatbot"}
                    data.GRIEVANCES.append(g)
                    st.success(T(f"Grievance {g['grievance_id']} registered.",
                                 f"ఫిర్యాదు {g['grievance_id']} నమోదైంది."))

    district = f["district_te"] if is_te() else f["district"]
    with st.expander(f"🌦️ {T('Weather', 'వాతావరణం')}  ·  {district}"):
        days = []
        for w in data.WEATHER[f["district"]]:
            icon = ("⛈️" if w["condition"] == "Thunderstorm" else "🌧️") if w["rain_mm"] else "☀️" if w["condition"] == "Sunny" else "⛅"
            d = date.fromisoformat(w["date"])
            rain = f'<small class="rain">{w["rain_mm"]}{T("mm", " మి.మీ.")}</small>' if w["rain_mm"] else ""
            days.append(f'<div class="wday" title="{e(w["condition_te"] if is_te() else w["condition"])}"><small>{day_label(d)}</small>'
                        f'<div class="wicon">{icon}</div><b>{w["max_c"]}°</b><small>{w["min_c"]}°</small>{rain}</div>')
        H(f'<div class="weather">{"".join(days)}</div>')

    crops = [c for c in f["crops"] if c in data.ADVISORIES]
    with st.expander(f"🌱 {T('Advisory', 'సలహాలు')}  ·  {', '.join(crop_name(c) for c in crops)}"):
        for c in crops:
            st.markdown(f"**{crop_name(c)}**")
            for tip in data.ADVISORIES[c][ss.ui_lang][:3]:
                st.markdown(f"- {tip}")


def page_my_details(user):
    """👤 My details (top-right menu): the farmer's details, land and crops, with Edit."""
    fid = user["farmer_id"]
    f = data.FARMER_INDEX[fid]
    if ss.get("editing") == fid:
        farm_edit(f, True)
    else:
        farm_profile(f, True, back=True)


def consent_screen(user):
    """🔒 Consent: shown once to every farmer before the app. Says what the app keeps and why;
    "I agree" opens the app, "No" logs out with a short message."""
    lang = ss.ui_lang
    t = consent.TEXT[lang]
    if lang == "te":
        ai.speak_later(consent.speech("te"), "te")  # start the Telugu voice now, so Read aloud is quick
    with st.container(key="topbar"):
        left, right = st.columns([2.6, 2.4], vertical_alignment="center")
        title = '<span class="te" style="margin:0">రైతు మిత్ర</span>' if is_te() else "Rythu Mitra"
        left.markdown(f'<div class="brand"><div class="logo">🌾</div><div class="brand-title">{title}</div></div>',
                      unsafe_allow_html=True)
        with right, st.container(horizontal=True, horizontal_alignment="right", key="topright"):
            lang_switch("lang_top")
    with st.container(key="consent_page"):
        keeps = "".join(f"<div><span>{icon}</span>{html.escape(line)}</div>" for icon, line in t["keeps"])
        uses = "".join(f"<li>{html.escape(u)}</li>" for u in t["uses"])
        promise = "".join(f"<li>✔️ {html.escape(p)}</li>" for p in t["promise"])
        H(f'<div class="consent"><div class="consent-icon">🔒</div><h2>{t["title"]}</h2><p>{t["intro"]}</p>'
          f'<div class="consent-keeps">{keeps}</div><h3>{t["use_title"]}</h3><ul>{uses}</ul>'
          f'<ul class="consent-promise">{promise}</ul><small>{t["law"]}</small></div>')
        c1, c2, c3 = st.columns([1, 1, 2])
        if c1.button("🔊 " + T("Read aloud", "చదివి వినిపించండి"), width="stretch", key="consent_speak"):
            speak_aloud(consent.speech(lang), lang)
        if c2.button("✖ " + t["decline"], width="stretch", key="consent_no"):
            consent.record(user["farmer_id"], False, lang)
            page_js("window.rmQuiet && rmQuiet()")
            log_out({"te": consent.TEXT["te"]["declined"], "en": consent.TEXT["en"]["declined"]})
        if c3.button("✅ " + t["agree"], type="primary", width="stretch", key="consent_yes"):
            consent.record(user["farmer_id"], True, lang)
            page_js("window.rmQuiet && rmQuiet()")
            st.rerun()


def first_details(user):
    """First login after sign-up: only the details form (and Log out) until it is saved."""
    if ss.pop("ask_logout", False):
        confirm_logout()
    with st.container(key="topbar"):
        left, right = st.columns([2.6, 2.4], vertical_alignment="center")
        title = '<span class="te" style="margin:0">రైతు మిత్ర</span>' if is_te() else "Rythu Mitra"
        left.markdown(f'<div class="brand"><div class="logo">🌾</div><div class="brand-title">{title}</div></div>',
                      unsafe_allow_html=True)
        with right, st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center",
                                 gap="small", key="topright"):
            lang_switch("lang_top")
            if st.button("🚪 " + T("Log out", "లాగ్ అవుట్"), key="setup_logout"):
                ss.ask_logout = True
                st.rerun()
    with st.container(key="setup_page"):
        farm_edit(data.FARMER_INDEX[user["farmer_id"]], True, setup=True)


def page_services(user):
    farmer_view = user["role"] == "farmer"
    if farmer_view:
        fid = user["farmer_id"]
    else:
        with st.container(key="panel_pick"):
            fid = st.selectbox("Farmer", [f["farmer_id"] for f in data.FARMERS],
                               format_func=lambda i: f"{i} · {data.FARMER_INDEX[i]['name']} · {data.FARMER_INDEX[i]['district']}")
    f = data.FARMER_INDEX[fid]
    # Details and chat on the left; on the right, rows that open when tapped
    left, right = st.columns([2.4, 1], gap="medium")
    with left:
        if farmer_view:  # just the greeting; details and Edit are under 👤 My details (top right)
            farm_profile(f, farmer_view, home=True)
        elif ss.get("editing") == fid:
            farm_edit(f, farmer_view)
        else:
            farm_profile(f, farmer_view)
        if farmer_view:  # farmers ask questions right here: type, or tap the mic and talk
            page_chat(user, embedded=True)
    with right, st.container(key="svc_side"):
        side_sections(f, fid)

    if not farmer_view:
        with st.container(key="panel_all_griev"):
            st.markdown("### All grievances")
            rows = sorted(data.GRIEVANCES, key=lambda g: g["created_on"], reverse=True)
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


# ---------------------------------------------------------------------------
# Crop health history (opened from the user menu, top right)
# ---------------------------------------------------------------------------

RESULT_ICON = {"cured": "✅", "improved": "👍", "no_change": "➖", "worse": "👎"}
RESULT_PILL = {"cured": "green", "improved": "green", "no_change": "amber", "worse": "red"}


def history_card(r, farmer_view, opts):
    """One diagnosis as 4 steps: spotted -> remedy given -> used? -> result."""
    e = html.escape
    when = datetime.fromisoformat(r["created_on"])
    fb = r["feedback"]
    if not fb:
        status = '<span class="pill amber">⏳ ' + T("Waiting for feedback", "మీ సమాధానం కోసం ఎదురుచూస్తోంది") + "</span>"
    elif fb["used"] == "no":
        status = '<span class="pill grey">' + T("Not used", "వాడలేదు") + "</span>"
    else:
        status = f'<span class="pill {RESULT_PILL[fb["result"]]}">{RESULT_ICON[fb["result"]]} {V(opts["results"][fb["result"]])}</span>'
    who = f'{e(r["farmer_name"])} ({r["farmer_id"]}), {r["district"]} · ' if not farmer_view else ""
    remedies = "".join(f'<small>{"🌿" if m["kind"] == "Organic" else "🧪"} {e(terms.medicine(m["product"], is_te()))}: {e(dose_te(m["dose"]))} · '
                       f'{T("buy", "కొనాల్సింది")} {e(m["total"])}</small>' for m in r["remedies"][:2])
    not_told = T("Not told yet", "ఇంకా చెప్పలేదు")
    used = not_told
    if fb:
        reason = fb.get("reason")
        reason = (FU_REASONS_TE.get(reason, reason) if is_te() else reason)
        used = V(opts["used"][fb["used"]]) + (f' — {e(terms.medicine(fb["product"], is_te()))}' if fb.get("product") else "") + \
            (f' — {e(reason)}' if reason else "")
        if fb.get("applied_on"):
            day = day_label(date.fromisoformat(fb["applied_on"]))
            used += "</small><small>" + T(f"Sprayed on {day}", f"{day} న పిచికారీ చేశారు")
    result = (f'{RESULT_ICON[fb["result"]]} {V(opts["results"][fb["result"]])}' if fb and fb.get("result")
              else "—" if fb else not_told)
    note = f'<small class="hist-note">“{e(fb["notes"])}”</small>' if fb and fb.get("notes") else ""
    plot = f' · {T("Plot", "భూమి ముక్క")} {e(r["plot"])}' if r.get("plot") else ""
    crop = e(crop_name(r["crop"]))
    if is_te():
        title = f'{crop}{plot} — {r["disease_te"]}'
        meta = (f'{who}{V(r["type"])} · {round(r["confidence"] * 100)}% నమ్మకం · {r["acres"]:g} ఎకరాలు · '
                f'{V(r["source"])} ద్వారా')
        spotted = f'{crop} పంటలో {r["disease_te"]}'
    else:
        title = f'{crop}{plot} — {e(r["disease"])}</b> <span class="te">{r["disease_te"]}</span><b>'
        meta = (f'{who}{r["type"]} · {round(r["confidence"] * 100)}% confidence · {r["acres"]:g} '
                f'{"acre" if r["acres"] == 1 else "acres"} · via {r["source"]}')
        spotted = f'{e(r["disease"])} on {crop}'
    H(f'''<div class="hist-card {'' if fb else 'pending'}">
<div class="hist-date"><b>{day_label(when)}</b><small>{time_label(when)}</small></div>
<div style="flex:1;min-width:0">
<div class="hist-head"><div><b class="hist-title">{title}</b>
<div class="muted">{meta}</div></div>{status}</div>
<div class="hist-steps">
<div><b>{T("Disease spotted", "తెగులు కనిపించింది")}</b><small>{spotted}</small></div>
<div><b>{T("Remedy given", "ఇచ్చిన మందు")}</b>{remedies}</div>
<div><b>{T("Used?", "వాడారా?")}</b><small>{used}</small></div>
<div><b>{T("Result", "ఫలితం")}</b><small>{result}</small>{note}</div>
</div>{photos_html(r)}</div></div>''')


def photos_html(r):
    """Crop photo when the disease was found, the medicine used, and the crop after the remedy."""
    urls = {k: history.photo_url(r, k) for k in history.PHOTO_KINDS}
    if not any(urls.values()):
        return ""

    def shot(kind, label):
        img = f'<img src="{urls[kind]}" alt="{label}">' if urls[kind] else \
            f'<div class="no-photo">{T("No photo", "ఫోటో లేదు")}</div>'
        on = (r.get("photos") or {}).get(kind)
        when = f'<small>{day_label(datetime.fromisoformat(on["on"]))}</small>' if on else ""
        return f'<figure class="hist-photo">{img}<figcaption><b>{label}</b>{when}</figcaption></figure>'
    return ('<div class="hist-photos">' + shot("before", T("Before remedy", "మందుకు ముందు"))
            + (shot("medicine", T("Medicine used", "వాడిన మందు")) if urls["medicine"] else "")
            + shot("after", T("After remedy", "మందు తర్వాత")) + "</div>")


FU_REASONS_TE = dict(FU_REASONS)


def go_home():
    """Back to the main page: Home for farmers, the chat for staff."""
    ss.pop("view", None)
    ss.page = "Farmer Services" if (current_user() or {}).get("role") == "farmer" else "Farmer Chat"


def page_password(user):
    """Change password (user menu): its own page, like My history."""
    with st.container(key="panel_password"):
        c1, c2 = st.columns([5, 1], vertical_alignment="center")
        c1.markdown("## 🔑 " + T("Change password", "పాస్‌వర్డ్ మార్చండి"))
        c2.button("← " + T("Back", "వెనక్కి"), width="stretch", key="pw_back", on_click=go_home)
        H('<p class="muted">' + T("Passwords need 8 or more characters, with letters and numbers.",
                                  "పాస్‌వర్డ్‌లో కనీసం 8 అక్షరాలు ఉండాలి — అక్షరాలు, అంకెలు రెండూ.") + "</p>")
        with st.form("change_pw", clear_on_submit=True, border=False):
            cur = st.text_input(T("Current password", "ప్రస్తుత పాస్‌వర్డ్"), type="password")
            n1 = st.text_input(T("New password", "కొత్త పాస్‌వర్డ్"), type="password")
            n2 = st.text_input(T("Confirm new password", "కొత్త పాస్‌వర్డ్ మళ్లీ రాయండి"), type="password")
            with st.container(horizontal=True, gap="small"):
                save = st.form_submit_button("💾 " + T("Save", "సేవ్ చేయండి"), type="primary")
                st.form_submit_button("🏠 " + T("Back to main page", "ముఖ్య పేజీకి వెళ్ళండి"), on_click=go_home)
            if save:
                try:
                    auth.change_password(user, cur, n1, n2)
                    st.success(T("Password changed.", "పాస్‌వర్డ్ మారింది."))
                except auth.AuthError as e:
                    st.error(err(e))


def history_actions(user):
    """⬇ Download saves the history as a page; 🖨️ Print opens the print box (which can also save a PDF)."""
    page = farm_report.build(user["farmer_id"], ss.ui_lang)
    with st.container(horizontal=True, gap="small", key="hist_actions", width="content"):
        st.download_button("⬇️ " + T("Download history", "చరిత్ర డౌన్‌లోడ్ చేయండి"), page,
                           file_name=f"farm-history-{user['farmer_id']}.html", mime="text/html", on_click="ignore")
        if st.button("🖨️ " + T("Print / Save as PDF", "ప్రింట్ / PDF గా సేవ్ చేయండి"), key="hist_print"):
            page_js(f"""(() => {{
  const frame = document.createElement('iframe');
  frame.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:0';
  frame.srcdoc = {json.dumps(page)};
  frame.onload = () => {{ frame.contentWindow.print(); setTimeout(() => frame.remove(), 60000); }};
  document.body.appendChild(frame);
}})();""")


def page_history(user):
    """Farm history (user menu): crops grown over time, and problems & remedies."""
    farmer_view = user["role"] == "farmer"
    # One compact header: title + Download / Print / Back on one line, then the section switch
    with st.container(key="panel_hist_head"):
        c1, c2 = st.columns([1, 1.6], vertical_alignment="center")
        c1.markdown("### 📜 " + (T("My farm history", "నా పొలం చరిత్ర") if farmer_view else T("Farm history", "పొలం చరిత్ర")))
        with c2, st.container(horizontal=True, horizontal_alignment="right", gap="small"):
            if farmer_view:
                history_actions(user)
            if st.button("← " + T("Back", "వెనక్కి"), key="hist_back"):
                ss.pop("view", None)
                st.rerun()
        st.caption(T("Crops grown on each plot, and every problem found by Crop Doctor with the remedy and how it worked.",
                     "ప్రతి భూమి ముక్కలో సాగు చేసిన పంటలు, పంట వైద్యుడు గుర్తించిన సమస్యలు, ఇచ్చిన మందు, అది ఎలా పనిచేసింది."))
        labels = {"crops": "🌱 " + T("Crops grown", "సాగు చేసిన పంటలు"),
                  "problems": "🩺 " + T("Problems & remedies", "సమస్యలు & నివారణలు")}
        section = st.segmented_control(T("Section", "విభాగం"), list(labels), key="hist_section", default="crops",
                                       format_func=labels.get, label_visibility="collapsed") or "crops"
    if section == "crops":
        page_crops(user)
    else:
        page_problems(user)


MONTH_FMT = "%b %Y"


def month_list(first="2015-01"):
    """Every month from `first` to this month, newest first."""
    y, m = map(int, first.split("-"))
    now = seasons.this_month()
    out = []
    while f"{y}-{m:02d}" <= now:
        out.append(f"{y}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out[::-1]


def plot_label(p):
    """'All plots' / 'Plot 123/A' / 'Plot Other' in the chosen language."""
    if p == "All plots":
        return T("All plots", "అన్ని భూమి ముక్కలు")
    p = p.removeprefix("Plot ")
    if p == "Other":
        return T("Plot Other", "ఇతర భూమి")
    return T(f"Plot {p}", f"భూమి ముక్క {p}")


def page_crops(user):
    farmer_view = user["role"] == "farmer"
    if farmer_view:
        fid = user["farmer_id"]
    else:
        fid = st.selectbox("Farmer", [f["farmer_id"] for f in data.FARMERS], key="crops_farmer",
                           format_func=lambda i: f"{i} · {data.FARMER_INDEX[i]['name']} · {data.FARMER_INDEX[i]['district']}")
    rows = seasons.records(fid)
    o = seasons.options(fid)
    now = o["this_month"]
    months = month_list()

    with st.container(key="panel_crops"):
        c1, c2, _ = st.columns([1, 1, 1.2], vertical_alignment="bottom")
        start_default = f"{int(now[:4]) - 2}-06"
        frm = c1.selectbox(T("From", "నుండి"), months, index=months.index(start_default), format_func=month_label, key="crops_from")
        to = c2.selectbox(T("To", "వరకు"), [m for m in months if m >= frm], format_func=month_label, key="crops_to")
        plots = list(dict.fromkeys(r["plot"] or "Other" for r in rows))
        plot = st.pills(T("Plot", "భూమి ముక్క"), ["All plots"] + [f"Plot {p}" for p in plots], default="All plots",
                        key=f"crops_plot_{fid}", format_func=plot_label) or "All plots"
        plot = None if plot == "All plots" else plot.removeprefix("Plot ")

        H('<div class="saved-note" style="font-weight:400;font-size:13px">' + T(
            "This is a saved record. When you change a crop on 🏠 My Details, it is added here automatically.",
            "ఇది సేవ్ అయిన రికార్డు. 🏠 నా వివరాలు లో పంట మార్చినప్పుడు ఇక్కడ దానంతట అదే చేరుతుంది.") + "</div>")

        in_range = [r for r in rows if r["start"] <= to and (r["end"] or now) >= frm]
        shown = [r for r in in_range if not plot or (r["plot"] or "Other") == plot]
        total = sum(r["yield_qtl"] or 0 for r in shown if not r["growing"])
        H(f'''<div class="farm-stats" style="margin-top:12px">
<div class="kpi"><small>{T("Crops in this period", "ఈ కాలంలో పంటలు")}</small><b>{len(shown)}</b></div>
<div class="kpi"><small>{T("Growing now", "ఇప్పుడు సాగులో ఉంది")}</small><b>{sum(r["growing"] for r in shown)}</b></div>
<div class="kpi"><small>{T("Different crops", "వేర్వేరు పంటలు")}</small><b>{len({r["crop"] for r in shown})}</b></div>
<div class="kpi"><small>{T("Total harvest", "మొత్తం దిగుబడి")}</small><b>{total:g} <span class="unit">{T("qtl", "క్వి.")}</span></b></div></div>''')
        H(f'<h3 style="margin-top:16px">🗓️ {T("Timeline", "కాలక్రమం")}: {month_label(frm)} – {month_label(to)}</h3>')
        H(gantt(rows, [p for p in plots if not plot or p == plot], frm, to, now))

        problems = history.records(fid)
        if not shown:
            H('<div class="empty">' + T("No crops in this period. Change the months above.",
                                        "ఈ కాలంలో పంటలు లేవు. పైన నెలలు మార్చండి.") + "</div>")
        last = None
        for r in shown:
            group = ("🌱 " + T("Growing now", "ఇప్పుడు సాగులో ఉంది") if r["growing"]
                     else "📅 " + T(f"Sown in {r['start'][:4]}", f"{r['start'][:4]} లో విత్తినవి"))
            if group != last:
                st.markdown(f"### {group}")
                last = group
            season_card(r, problems, now)


SEASON_CLASS = {"Kharif": "kharif", "Rabi": "rabi", "Summer": "summer", "Both": "both"}
MONTH_INITIALS_TE = ["జ", "ఫి", "మా", "ఏ", "మే", "జూ", "జు", "ఆ", "సె", "అ", "న", "డి"]


def gantt(rows, plots, frm, to, now):
    """Bars per plot showing which crop was on the land in which months."""
    def idx(m):
        y, mm = map(int, m.split("-"))
        return y * 12 + mm - 1
    lo, hi = idx(frm), idx(to)
    span = max(1, hi - lo + 1)

    def pos(m):
        return f"{(m - lo) / span * 100:.3f}%"

    # Year bands (shaded, year name in the middle) and a row of month letters
    bands = [(y, max(y * 12, lo), min(y * 12 + 12, hi + 1)) for y in range(lo // 12, hi // 12 + 1)]
    axis = "".join(f'<span class="g-band {"odd" if y % 2 else ""}" style="left:{pos(a)};width:{(b - a) / span * 100:.3f}%">'
                   f'{y if b - a >= 2 else ""}</span>' for y, a, b in bands)
    bg = "".join(f'<span class="g-bg {"odd" if y % 2 else ""}" style="left:{pos(a)};width:{(b - a) / span * 100:.3f}%"></span>'
                 for y, a, b in bands)
    out = f'<div class="gantt"><div class="g-axis"><span class="g-name"></span><div class="g-track">{axis}</div></div>'
    if span <= 48:
        initials = MONTH_INITIALS_TE if is_te() else "JFMAMJJASOND"
        letters = "".join(f'<span style="left:{pos(m)};width:{100 / span:.3f}%">{initials[m % 12]}</span>'
                          for m in range(lo, hi + 1))
        out += f'<div class="g-axis g-months"><span class="g-name"></span><div class="g-track">{letters}</div></div>'
    for p in plots:
        # A crop fills its months from the start of the sowing month to the end of the harvest
        # month. If the next crop is sown in the month the last one was harvested, they share it.
        spans = [[r, idx(r["start"]), idx(r["end"] or now) + 1]
                 for r in sorted((r for r in rows if (r["plot"] or "Other") == p), key=lambda r: r["start"])]
        for prev, cur in zip(spans, spans[1:]):
            if prev[2] - 1 == cur[1]:
                prev[2] = cur[1] = cur[1] + 0.5
        bars = ""
        for r, a, b in spans:
            if b <= lo or a >= hi + 1:
                continue
            a, b = max(a, lo), min(b, hi + 1)
            tip = (f'{crop_name(r["crop"])} · {V(r["season"])} · {month_label(r["start"])} – '
                   f'{month_label(r["end"]) if r["end"] else T("now", "ఇప్పటివరకు")}')
            bars += (f'<div class="g-bar {SEASON_CLASS.get(r["season"], "")} {"now" if r["growing"] else ""}" title="{html.escape(tip)}" '
                     f'style="left:{pos(a)};width:calc({(b - a) / span * 100:.3f}% - 2px)">'
                     f'{data.crop_icon(r["crop"])} {html.escape(crop_name(r["crop"]).split(" (")[0])}</div>')
        out += (f'<div class="g-row"><span class="g-name">{html.escape(plot_label("Plot " + p))}</span>'
                f'<div class="g-track">{bg}{bars}</div></div>')
    return out + ('<div class="g-legend">' + T(
        '<span><i class="kharif"></i> Kharif (monsoon)</span><span><i class="rabi"></i> Rabi (winter)</span>'
        '<span><i class="summer"></i> Summer</span><span><i class="both"></i> Both</span><span><i class="now"></i> Growing now</span>',
        '<span><i class="kharif"></i> ఖరీఫ్ (వానాకాలం)</span><span><i class="rabi"></i> రబీ (చలికాలం)</span>'
        '<span><i class="summer"></i> వేసవి</span><span><i class="both"></i> రెండు సీజన్లు</span>'
        '<span><i class="now"></i> ఇప్పుడు సాగులో ఉంది</span>') + '</div></div>')


def season_card(r, problems, now):
    e = html.escape
    probs = [p for p in problems if p["crop"] == r["crop"] and r["start"] <= p["created_on"][:7] <= (r["end"] or now)]
    meta = []
    if r["yield_qtl"] is not None:
        per = r["yield_qtl"] / r["area_acres"]
        meta.append(T(f'🧺 Harvest {r["yield_qtl"]:g} qtl ({per:.1f} qtl/acre)',
                      f'🧺 దిగుబడి {r["yield_qtl"]:g} క్వి. (ఎకరానికి {per:.1f} క్వి.)'))
    if probs:
        if is_te():
            meta.append(f'🩺 {len(probs)} సమస్యలు: {e(", ".join(dict.fromkeys(p["disease_te"] for p in probs)))}')
        else:
            meta.append(f'🩺 {len(probs)} problem{"s" if len(probs) > 1 else ""}: {e(", ".join(dict.fromkeys(p["disease"] for p in probs)))}')
    meta.append(f'📝 {e(V(r["source"]))}')
    if r.get("notes"):
        meta.append(f'“{e(r["notes"])}”')
    status = ('<span class="pill green">🌱 ' + T("Growing now", "ఇప్పుడు సాగులో ఉంది") + "</span>" if r["growing"]
              else '<span class="pill grey">✅ ' + T("Harvested", "కోత పూర్తయింది") + "</span>")
    plot = f' · {T("Plot", "భూమి ముక్క")} {e(r["plot"])}' if r.get("plot") else ""
    months = T("month" if r["months"] == 1 else "months", "నెలలు" if r["months"] != 1 else "నెల")
    expected = (f' 🧺 {T("harvest expected", "కోత అంచనా")} {month_label(r["expected_end"])} ·'
                if r["growing"] and r.get("expected_end") else "")
    H(f'''<div class="season-card"><div class="plot-crop">{data.crop_icon(r["crop"])}</div><div style="flex:1;min-width:0">
<div class="hist-head"><b>{e(crop_name(r["crop"]))}{plot}</b>{status}</div>
<div class="season-when"><b>{month_label(r["start"])} → {month_label(r["end"]) if r["end"] else T("now", "ఇప్పటివరకు")}</b> ·{expected}
{r["months"]} {months} · {V(r["season"])} · {r["area_acres"]:g} {T("acres", "ఎకరాలు")}</div>
<div class="plot-meta">{"".join(f"<span>{m}</span>" for m in meta)}</div></div></div>''')


def page_problems(user):
    farmer_view = user["role"] == "farmer"
    rows = history.records(user["farmer_id"] if farmer_view else None)
    s = history.summary(rows)
    opts = history.options()
    if is_te():
        H('<div class="saved-note" style="font-weight:400;font-size:13px">🩺 ' +
          ("మీ పంటల్లో కనిపించిన సమస్యలు" if farmer_view else "అందరు రైతుల పంటల్లో కనిపించిన సమస్యలు") +
          ", సూచించిన మందు, వాడారా లేదా, ఎలా పనిచేసింది." +
          (" పిచికారీ చేసిన తర్వాత ఫలితాన్ని పైన 🔔 గంటలో చెప్పండి — ఇది ఇతర రైతులకు కూడా సహాయపడుతుంది." if farmer_view else "") + "</div>")
    else:
        H('<div class="saved-note" style="font-weight:400;font-size:13px">🩺 ' +
          ("Problems found on your crops" if farmer_view else "Problems found for all farmers") +
          ", the remedy suggested, whether it was used, and how it worked." +
          (" After you spray, tell us the result from the 🔔 bell at the top — it helps other farmers too." if farmer_view else "") + "</div>")
    pct = "—" if s["worked_pct"] is None else f'{s["worked_pct"]}%'
    H(f'''<div class="farm-stats">
<div class="kpi"><small>{T("Problems found", "కనిపించిన సమస్యలు")}</small><b>{s["cases"]}</b></div>
<div class="kpi"><small>{T("Waiting for feedback", "మీ సమాధానం కోసం ఎదురుచూస్తోంది")}</small><b class="{'warn' if s['pending'] else ''}">{s["pending"]}</b></div>
<div class="kpi"><small>{T("Remedy used", "మందు వాడినవి")}</small><b>{s["used"]}</b><small>{T(f'{s["not_used"]} not used', f'{s["not_used"]} వాడలేదు')}</small></div>
<div class="kpi"><small>{T("Remedy worked", "మందు పనిచేసింది")}</small><b>{pct}</b><small>{T(f'{s["worked"]} of {s["used"]} cured or improved', f'{s["used"]} లో {s["worked"]} తగ్గాయి లేదా మెరుగుపడ్డాయి')}</small></div>
</div>''')

    with st.container(key="panel_hist_list"):
        c1, c2 = st.columns([2, 1.2], vertical_alignment="bottom")
        with c1:
            show = seg(T("Show", "చూపించు"), ["all", "pending", "done"], "hist_filter",
                       {"all": T("All", "అన్నీ"), "pending": T("Waiting", "ఎదురుచూస్తున్నవి") + f" ({s['pending']})",
                        "done": T("Feedback given", "సమాధానం ఇచ్చినవి")})
        search = "" if farmer_view else c2.text_input("Search", placeholder="Farmer, crop or disease", key="hist_search")
        shown = [r for r in rows if (show == "all" or (show == "pending") == (not r["feedback"]))
                 and search.lower() in f'{r["farmer_id"]} {r["farmer_name"]} {r["crop"]} {r["disease"]}'.lower()]
        if not shown:
            H('<div class="empty"><div style="font-size:34px">🌱</div>' +
              (T("Nothing here for this filter.", "ఇక్కడ ఏమీ లేవు.") if rows else
               T("No history yet. Use <b>Crop Doctor</b> to check a sick plant — the result is saved here.",
                 "ఇంకా చరిత్ర లేదు. జబ్బు పడిన మొక్కను <b>పంట వైద్యుడు</b> లో చూపించండి — ఫలితం ఇక్కడ సేవ్ అవుతుంది.")) + "</div>")
        last_month = None
        for r in shown:
            m = month_label(r["created_on"][:7])
            if not is_te():
                m = datetime.fromisoformat(r["created_on"]).strftime("%B %Y")
            if m != last_month:
                st.markdown(f"### 📅 {m}")
                last_month = m
            history_card(r, farmer_view, opts)
            if farmer_view and not r["feedback"]:
                st.caption("🔔 " + T("Answer the questions about this remedy from the bell at the top.",
                                     "ఈ మందు గురించి ప్రశ్నలకు పైన 🔔 గంటలో సమాధానం ఇవ్వండి."))


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
        if ss.get("view") == "about" and st.columns([5, 1])[1].button("← " + T("Back", "వెనక్కి"), width="stretch",
                                                                       key="about_back"):
            ss.pop("view", None)
            st.rerun()
        if is_te():
            st.markdown("""
## యాప్ ఎలా పనిచేస్తుంది

**రైతు మిత్ర** భారత్ విస్తార్‌తో కలిపిన తెలంగాణ రాష్ట్ర సమాచార వ్యవస్థకు ఒక నమూనా (ప్రయోగాత్మక) యాప్.
ఇందులోని సమాచారం అంతా చూపించడం కోసం పెట్టిన **నమూనా సమాచారం**.

**మాక్ AI మోడ్ (మొదట ఇదే, API కీలు అవసరం లేదు).** ప్రశ్నను అర్థం చేసుకోవడం (విషయం, తెలుగు/ఇంగ్లీష్, పంట, జిల్లా),
సమాచారం వెతకడం (ధరలు, వాతావరణం, పథకాలు, రైతు రికార్డులు, రాష్ట్ర సర్క్యులర్లు) నిజంగానే జరుగుతాయి. చివరి సమాధానం
మాత్రమే నమూనా వాక్యాలతో రాస్తాము — Claude-మాక్ పాయింట్లుగా, ChatGPT-మాక్ చిన్న నంబర్ల జాబితాగా. సమయం, టోకెన్ల లెక్కలు
కూడా నమూనావే. ఫోటో పరీక్షలో ఫోటోను చూడకుండా సమాచారం నుండి ఒక సమస్యను ఎంచుకుంటాము.

**లైవ్ మోడ్.** `ANTHROPIC_API_KEY` మరియు/లేదా `OPENAI_API_KEY` పెట్టండి (మీ కంప్యూటర్‌లో `backend/.env` లో, లేదా Streamlit Cloud →
Settings → Secrets లో). అప్పుడు నిజమైన AI మోడళ్లు అదే సమాచారంతో సమాధానాలు రాస్తాయి, పంట ఫోటోలను చూస్తాయి.

**భద్రత.** పంట వైద్యుడులో AI సమస్యను మాత్రమే గుర్తిస్తుంది. మందు మోతాదులు ఎప్పుడూ పరిశీలించిన పట్టిక నుండే వస్తాయి.

| పేజీ | ప్రతిపాదన |
|---|---|
| లాగిన్ | §2.8 అడ్మిన్ / కంట్రిబ్యూటర్ / సమీక్షకుల పాత్రలు |
| రైతు చాట్ | దశ 1 చాట్‌బాట్ & వాయిస్ బాట్, §2.6 ఛానల్స్ |
| పంట వైద్యుడు | §2.7 ఫోటోతో పంట/పురుగు గుర్తింపు |
| Claude vs ChatGPT | §2.9 అంగీకరించిన పరీక్షలతో పోలిక |
| Content Pipeline | దశ 2, §2.4 సమాచార పైప్‌లైన్ |
| రైతు సేవలు / నా వివరాలు | దశలు 3 & 4 — దరఖాస్తులు, డబ్బు జమ, ఫిర్యాదులు, భూమి |
| PMU Dashboard | §2.9 పర్యవేక్షణ & నివేదికలు, §2.10 PMU |
""")
            return
        st.markdown("""
## How the app works

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
init_lang()
profiles.sync()  # pick up profile edits saved by the React app
applications.sync()  # and scheme applications made there
user = current_user()
if not user and not ss.get("on_login"):
    ss.ui_lang = "te"  # the login page always opens in Telugu; the switch changes it
    init_lang()
ss.on_login = not user
if is_te():
    H(TE_CSS)
if ss.pop("save_cookie", False):
    remember_login(ss.get("token"))
if user and ss.get("token") and st.query_params.get("s") != ss.token:
    st.query_params["s"] = ss.token  # so a refresh stays logged in on Streamlit Cloud too
if ss.pop("save_lang", False):
    remember_lang()
if not user:
    ss.pop("token", None)
    if ss.get("logged_out") and not ss.get("cookie_cleared"):
        remember_login(None)
        ss.cookie_cleared = True
    st.query_params.clear()
    page_js("document.getElementById('wa-float')?.remove()")
    auth_screen()
elif user["role"] == "farmer" and not consent.given(user["farmer_id"]):
    consent_screen(user)  # every farmer agrees once before using the app
elif user["role"] == "farmer" and profiles.needs_details(user["farmer_id"]):
    first_details(user)  # a farmer who just signed up fills My Details before anything else
else:
    page = header(user)
    staff = user["role"] != "farmer"
    with st.container(key="content"):
        if page == "History":
            page_history(user)
        elif page == "My details" and not staff:
            page_my_details(user)
        elif page == "Change password":
            page_password(user)
        elif page == "Farmer Chat":
            page_chat(user)
        elif page == "Crop Doctor":
            page_doctor(user)
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
