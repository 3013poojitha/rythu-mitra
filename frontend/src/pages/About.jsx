export default function About() {
  return (
    <div className="stack narrow">
      <div className="panel">
        <h2>What is Mock AI mode?</h2>
        <p>
          The app is built to use two real AI models — <b>Claude</b> (Anthropic) and <b>ChatGPT</b> (OpenAI). Calling them needs paid
          API keys. Until keys are available, the app runs in <b>Mock AI mode</b>:
        </p>
        <ul>
          <li><b>No keys, no internet, no cost.</b> Everything runs on your laptop.</li>
          <li>The <b>retrieval</b> part is real: the backend works out what the farmer is asking (price, weather, scheme, pest…), detects Telugu or English, and looks up the answer in the dummy data.</li>
          <li>The <b>writing</b> part is simulated: instead of an AI model phrasing the reply, templates fill in the facts. "Claude (mock)" writes in a warm bullet style and "ChatGPT (mock)" in a short numbered style, so the comparison screen still shows a difference.</li>
          <li>Latency and token counts are <b>simulated</b> so the dashboards and comparison look realistic.</li>
          <li>Photo diagnosis picks a pest from a small library based on the image — it does not really look at the photo.</li>
        </ul>
        <h3>Switching to real AI later</h3>
        <ol>
          <li>Get an API key from console.anthropic.com and/or platform.openai.com.</li>
          <li>Copy <code>backend/.env.example</code> to <code>backend/.env</code> and paste the keys.</li>
          <li>Restart the backend. The badge at the top turns green ("Live"). No code changes needed — the same facts are now sent to the real model, which writes the answer and can really read crop photos.</li>
        </ol>
      </div>

      <div className="panel">
        <h2>How the app maps to the proposal</h2>
        <table>
          <thead><tr><th>Proposal</th><th>Where in the app</th></tr></thead>
          <tbody>
            <tr><td>Stage 1 — Core chatbot & voice bot (Telugu)</td><td>Farmer Chat: Telugu/English, mic input, spoken replies</td></tr>
            <tr><td>Stage 2 — Publishing Department content</td><td>Content Pipeline: 11-stage ingestion with Contributor / Reviewer / BV roles</td></tr>
            <tr><td>Stage 3 — API-based personalised services</td><td>Enter a Farmer ID in chat → application, payment and grievance status</td></tr>
            <tr><td>Stage 4 — Deep system integration</td><td>Land & crop records drive tailored advice; Farmer Services screen</td></tr>
            <tr><td>Channel expansion — Website & WhatsApp</td><td>Channel switch in Farmer Chat (Web / WhatsApp / Voice)</td></tr>
            <tr><td>§2.7 Image-based crop/pest diagnosis</td><td>📷 button in Farmer Chat</td></tr>
            <tr><td>§2.9 Governance, testing against agreed scenarios</td><td>Claude vs ChatGPT tab (test runner) and PMU Dashboard</td></tr>
          </tbody>
        </table>
      </div>

      <div className="panel">
        <h2>Architecture</h2>
        <pre className="arch">{`React frontend (Vite)
   │  /api/*
FastAPI backend (Python)
   ├── assistant.py  → understands the question, fetches facts (retrieval)
   ├── ai.py         → Claude / ChatGPT, live or mock, writes the reply
   ├── pipeline.py   → 11-stage content ingestion
   └── data.py       → dummy farmers, schemes, mandi prices, weather, pests`}</pre>
        <p className="muted">All data is fictional and generated for demonstration only.</p>
      </div>
    </div>
  );
}
