# Rythu Mitra — Telangana × Bharat Vistaar prototype

A working prototype of the **Telangana State Intelligence Layer integrated with Bharat Vistaar**
(NISG techno-commercial proposal for the Agriculture Department, Government of Telangana).
It covers all four stages from the proposal, plus the extra channels and the PMU governance work,
using **dummy data** and **two AI model families: Claude (Anthropic) and ChatGPT (OpenAI)**.

> All data in this app is fictional and for demonstration only.

## Run it

**Easiest (Windows):** double-click `start.bat`. It installs everything on first run and opens http://localhost:8000.

**Manual:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
cd ../frontend
npm install
npm run build
cd ..
backend\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --port 8000
```

Open http://localhost:8000.

**While developing the UI** (hot reload): keep the backend running, then run `npm run dev` in `frontend/` and open http://localhost:5173.

Requirements: Python 3.10+ and Node.js 18+.

## Streamlit version

`streamlit_app.py` is a Streamlit version of the same app. It has the same login, chat, Crop Doctor, services, pipeline and dashboard, and reuses the Python logic in `backend/app/`.

Run it locally:

```bash
backend\.venv\Scripts\pip install -r requirements.txt
backend\.venv\Scripts\streamlit run streamlit_app.py
```

Deploy it free on Streamlit Community Cloud:
1. Go to https://share.streamlit.io and sign in with GitHub.
2. Click **Create app**, then **Deploy a public app from GitHub**.
3. Repository `3013poojitha/rythu-mitra`, branch `main`, main file `streamlit_app.py`.
4. Under **Advanced settings**, choose Python 3.11, then click **Deploy**.
5. Optional live AI: in the app's **Settings → Secrets**, add `ANTHROPIC_API_KEY = "..."` and/or `OPENAI_API_KEY = "..."`.

## Deploy online (Render, free)

1. Push this folder to a GitHub repository (private is fine).
2. On https://render.com, sign in with GitHub, choose **New → Blueprint**, and pick the repository. Render reads `render.yaml` and builds the app.
3. When it finishes you get a link like `https://rythu-mitra.onrender.com`.

Notes:
- The UI is pre-built in `frontend/dist`. After changing anything in `frontend/src`, run `npm run build` in `frontend/`, then commit and push. Render redeploys automatically.
- The free plan sleeps after 15 minutes without visitors. The first visit after that takes about a minute to wake up, so open the link a few minutes before a demo.
- Data and changed passwords reset on every restart or redeploy (demo behaviour).
- To switch on live AI, add `ANTHROPIC_API_KEY` and/or `OPENAI_API_KEY` in the Render dashboard under **Environment**.

## Demo accounts

| Role | User ID | Password | Sees |
|---|---|---|---|
| Department Admin | `admin` | `Admin@123` | Everything; can act as any role in the Content Pipeline |
| NISG Contributor | `nisg.contributor` | `Contrib@123` | Staff tabs; uploads documents and does Contributor steps |
| Department Reviewer | `dept.reviewer` | `Review@123` | Staff tabs; does Reviewer approval steps |
| Bharat Vistaar Central | `bv.central` | `Central@123` | Staff tabs; publishes to production |
| Farmer (Anitha Reddy) | `TS1002` | `Farmer@123` | Home (with the chat), Crop Doctor, 📅 Today, 🔔 bell, My details, My history (own records only) |
| More farmers | `TS1001`, `TS1003` to `TS1011` | `Farmer@123` | Same as TS1002, each with their own land, crops and schemes |

Accounts are saved in `backend/users.json`. Delete that file and restart to reset every account back to this table.

## My Details (farmer home screen)

A farmer who logs in lands on **🏠 My Details** first. It shows their name, village, total land, crops and each land plot (survey number, acres, crop, season, soil, water source, and when the crop was sown and is expected to be harvested, with the days left). **✏️ Edit details** lets them change their personal details and add, edit or remove plots, including the optional **🌱 Sown on** and **🧺 Harvest by** dates. Total acres and the crop list are recalculated from the plots. Mobile and bank stay read-only.

Under the details is **💬 the chat** (one chat for typing and talking, see below). On the right side are five rows - 📋 Scheme applications, 💰 Payment status, 📣 Grievances, 🌦️ Weather and 🌱 Advisory - each with an icon, a short hint and a **›**; tap a row to open what it contains. On a phone the rows move under the chat.

**One chat for typing and talking.** Type a question, tap a quick question, or tap **🎤**: the app says a welcome aloud in the chosen language ("రైతు మిత్రకు స్వాగతం. ఇప్పుడు మీరు మాట్లాడి మీ ప్రశ్న అడగవచ్చు." / "Welcome to Rythu Mitra. You can now talk and ask your question."), then listens, and reads the answer back. The full welcome plays the first time; after that a short "Please ask your question". Listening needs Chrome or Edge. A **📷** crop photo can be sent in the same chat. Staff still have a **Farmer Chat** tab to test any farmer. The floating **WhatsApp** button opens the same chat in WhatsApp style.

Edits are saved in `backend/farmer_profiles.json` (logic in `backend/app/profiles.py`) and the chatbot uses them straight away. The React and Streamlit apps share this file, so an edit in one shows in the other. Logins are kept in `backend/sessions.json`, so restarting the server does not log anyone out. Delete that file and restart to reset every farmer to the demo data. Staff can edit any farmer from **Farmer Services**.

## Telugu first (తెలుగు | English)

The app opens in **Telugu**, because most Telangana farmers read Telugu, not English. A **తెలుగు | English** switch sits in the top bar and on the login card, and the browser remembers the choice. Every farmer screen follows it: login, My Details, Farmer Chat (the bot replies in the chosen language), Crop Doctor (including the spray instructions), History, the chat follow-up questions and How the app works. Data values (soil, water source, season, statuses, months) and error messages are shown in Telugu too. Medicine names show in Telugu with the English bottle label in brackets, e.g. పైమెట్రోజిన్ 50 WG (Pymetrozine 50 WG), so farmers can read them and still match the bottle in the shop. The login page always opens in Telugu. Switching to English changes everything, including earlier chat answers. Staff-only pages (Claude vs ChatGPT, Content Pipeline, PMU Dashboard) stay in English.

The shared Telugu words are in `backend/app/terms.py` (served to the React app at `/api/terms`); the React language switch is in `frontend/src/i18n.jsx`.

## Login & account features

- **Log in** with user ID and password; **Remember me** keeps you signed in after closing the browser.
- **Farmer sign-up**: a farmer creates an account with their Farmer ID plus the mobile number on the department record, so someone else can't claim their ID.
- **Forgot password → Reset password**: enter your user ID and a 6-digit code is "sent" to the registered mobile. There is no real SMS in this prototype, so the code is shown on screen and printed in the server window. The code expires in 10 minutes and allows 5 tries.
- **Change password** from the user menu (top right) opens its own page, with **🏠 Back to main page**. **Log out** asks "Log out?" first, with Cancel.
- **Security basics**: passwords are stored only as salted hashes (PBKDF2). The account locks for 5 minutes after 5 wrong passwords. Passwords need 8+ characters with letters and numbers. Sessions expire after 8 hours and survive a server restart, and a password reset signs out all devices.
- **Role-based access**: farmers only see and query their own records. Staff-only pages and APIs (Compare, Pipeline, Dashboard) are blocked for farmers in the backend, not just hidden in the UI.

## Farm history (user menu → 📜 My history)

The History page has two parts:

**🌱 Crops grown** — which crop was on which plot, from which month to which month. A timeline shows one row per plot with a bar for each crop (green = Kharif, orange = Rabi, striped = growing now), and a list grouped by year shows the months, season, acres, harvest in quintals (and per acre), and any Crop Doctor problems found during that crop. Choose the **From** and **To** months to see any period, and filter by plot. History is a saved record only - nothing is edited here. The first time it opens, two years of past seasons are filled in from demo department records. Changing a plot's crop in **My Details** automatically closes the old crop this month and starts the new one (from the sowing month, if a **Sown on** date was given; a **Harvest by** date shows as "harvest expected").

**⬇️ Download history** saves the whole history (farmer details, crops grown, problems & remedies with photos) as one page in Telugu or English; **🖨️ Print / Save as PDF** opens the print box, which can also save it as a PDF (`backend/app/report.py`, `/api/history/report`). Saved in `backend/crop_seasons.json` (logic in `backend/app/seasons.py`).

**🩺 Problems & remedies** — described below.

## Crop health history (Crop Doctor follow-up)

Every disease Crop Doctor finds for a farmer (from a photo in Crop Doctor or in the chat) is saved automatically, together with that photo. Open **📜 My history** from the user menu (top right, above Log out). Each entry shows: the disease spotted on which crop and plot, the remedy given (dose and how much to buy), whether the farmer used it, the result (cured, improved, no change, got worse), and the photos **Before remedy → Medicine used → After remedy**. Entries are grouped by month, and the top shows how many cases are waiting and how often the remedy worked. Staff see every farmer's history with a search box.

**🔔 The bell asks the questions.** A bell next to the user menu shows how many remedies are waiting. Tapping it asks one question at a time (in Telugu or English): did you use it → which product → when did you spray → how did it work (or why not). If the remedy was used, it then asks for a **💊 picture of the medicine used** and a **📷 photo of the crop now** (both optional). The answers and photos are saved to History and the count goes down. The chat no longer asks these questions.

Saved in `backend/crop_history.json`, photos in `backend/crop_photos/` (logic in `backend/app/history.py`).

## Crop Doctor (disease detection & spray guide)

1. Upload or take a photo of the affected plant. Optionally choose the crop and enter your field size in acres.
2. You get the disease or pest name, a confidence score, why it happens, and the symptoms to confirm.
3. The treatment plan gives chemical and organic options. For each one it shows:
   - the **dose per litre**
   - the amount **per 16-litre sprayer tank**
   - the **number of tanks** and **total water** for your acres
   - the **total product to buy**
   - when to spray, when to repeat, how to apply, and the **waiting period before harvest**
4. It also lists prevention tips and safety steps for spraying.
5. The **Disease library** lets you browse 13 common problems across paddy, cotton, maize, chilli, red gram, groundnut, turmeric and soybean without a photo.

**Safety by design:** the AI model only *identifies* the problem. Doses always come from the vetted table in `backend/app/diseases.py`, so the AI can never invent a chemical dose. The doses are demo values based on common published recommendations. A real deployment must use the State's approved package of practices.

## Mock AI mode (the default — no API keys needed)

The app is built to call real Claude and ChatGPT models, but runs without keys in **Mock AI mode**:

| Part | Mock mode | Live mode (with keys) |
|---|---|---|
| Understanding the question (intent, Telugu/English, crop, district) | Real (rule-based) | Same |
| Looking up facts (prices, weather, schemes, farmer records, State circulars) | Real (dummy data) | Same |
| Writing the reply | Templates; Claude-mock = warm bullet style, ChatGPT-mock = short numbered style | Real model writes the reply from the same facts |
| Latency and token counts | Simulated | Real |
| Pest photo diagnosis | Picks from a pest library based on the image | Real vision model looks at the photo |
| Telugu→English translation in the content pipeline | Copies the original with a note | Real translation |

**Switching to live:** copy `backend/.env.example` to `backend/.env`, add `ANTHROPIC_API_KEY` and/or `OPENAI_API_KEY`, and restart. The badges in the header turn green. You can add just one key; the other model stays in mock mode. If a live call fails, the app falls back to the mock answer and shows a note, so a demo never breaks.

## Screens and how they map to the proposal

| Tab | Proposal section | What to show |
|---|---|---|
| **Login** | §2.8 Admin / Contributor / Reviewer roles | Log in, sign up, forgot/reset password, role-based tabs |
| **Chat** (on My Details for farmers; tab for staff) | Stage 1 chatbot & voice bot; §2.6 Website/WhatsApp; §2.7 image diagnosis | Telugu or English questions; one chat for typing and 🎤 talking (spoken welcome and spoken replies, Chrome/Edge); floating WhatsApp button; 📷 pest photo |
| **Crop Doctor** | §2.7 image-based crop/pest diagnosis | Photo → disease → spray plan with quantities for your acres |
| **Claude vs ChatGPT** | §2.9 testing against agreed scenarios | Same question to both models side by side; "Run all tests" scores 8 agreed scenarios |
| **Content Pipeline** | Stage 2; §2.4 ingestion pipeline | 11 stages with Contributor / Reviewer / Bharat Vistaar roles; only Completed documents feed the chatbot |
| **Farmer Services** | Stage 3 APIs; Stage 4 land & crop data | Applications, payments, grievances (raise a new one), land plots, weather, tailored advisory |
| **PMU Dashboard** | §2.9 governance & reporting; §2.10 PMU | Usage KPIs, topics, channels, districts, integration tracker, risks & issues register |
| **How it works** | — | Explains Mock AI mode and the architecture |

## 5-minute demo script

0. Log in as `admin`. To show the login features, log out and use **Forgot password** for `TS1002`, then log in as that farmer to show the limited farmer view and the **Crop Doctor** (upload a photo, set acres to 2.5, and point out the quantities). Then log back in as `admin`.
1. **Farmer Chat** → click `రైతు భరోసా పథకం గురించి చెప్పండి`. The answer is in Telugu, tagged *Stage 2 – State content*, and cites the published State circular.
2. Switch the language to English and click *What is my application status?* → the bot asks for a Farmer ID (consent and login).
3. Enter `TS1002`, switch the channel to **WhatsApp**, and ask again → a personalised status (*Stage 3*).
4. Ask *fertilizer advice for my crop* → advice tailored to the farmer's soil, irrigation and weather (*Stage 4*).
5. Click 📷 and upload any crop photo → a pest diagnosis with the remedy.
6. **Claude vs ChatGPT** → click Compare, then **Run all tests** → 8/8 pass for each model.
7. **Content Pipeline** → open *Rabi 2026 seasonal crop advisory*, set "Acting as" to Reviewer, and approve; switch to Admin to finish. Back in Farmer Chat, ask *When to sow Bengal gram?* — the bot now answers from the document you just published.
8. **PMU Dashboard** → KPIs, the integration tracker by stage, and the risk register.

## Project structure

```
backend/
  app/main.py        FastAPI routes (/api/...), login check, serves the built frontend
  app/auth.py        Users, password hashing, login sessions, forgot/reset password
  app/diseases.py    Crop Doctor disease library with spray doses
  app/assistant.py   Intent detection + fact retrieval (Stages 1-4)
  app/ai.py          Claude / ChatGPT providers, live or mock
  app/pipeline.py    11-stage content ingestion pipeline
  app/data.py        Dummy farmers, schemes, mandi prices, weather, pests, tracker
frontend/
  src/pages/         Chat, Compare, Pipeline, Services, Dashboard, About
  src/api.jsx        API client
start.bat            One-click start on Windows
```

## API quick reference

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/login`, `/api/auth/logout` | Log in (returns a token) / log out |
| POST | `/api/auth/register` | Farmer sign-up |
| POST | `/api/auth/forgot-password`, `/api/auth/reset-password` | Password reset with a one-time code |
| POST | `/api/auth/change-password` · GET `/api/auth/me` | Change password / current user |
| GET | `/api/diseases?acres=2` | Disease library with spray quantities |
| GET | `/api/status` | Which models are live or mock |
| POST | `/api/chat` | `{message, provider: "claude"|"gpt", farmer_id?, channel?}` |
| POST | `/api/compare` | The same question to both models |
| POST | `/api/diagnose` | multipart `file`, `provider`, `lang` → pest diagnosis |
| POST | `/api/evaluate` | Run the agreed test scenarios on both models |
| GET | `/api/farmers`, `/api/farmers/{id}` | Farmer records (Stages 3/4) |
| GET/POST | `/api/grievances` | List / raise grievances |
| GET/POST | `/api/documents`, `/api/documents/{id}/advance` | Content pipeline |
| GET | `/api/dashboard` | PMU dashboard data |

Interactive API docs: http://localhost:8000/docs

## Notes and limits

- Data lives in memory and resets when the server restarts. That's intentional for a demo; swap `data.py` for a database to keep it.
- Intent detection is keyword-based. In live mode the model writes better answers, but routing is still rule-based. A next step would be to let the model choose tools (function calling).
- Voice input uses the browser's Web Speech API (Chrome or Edge).
