import { useLang } from "../i18n.jsx";

// "How the app works": Mock AI mode, how it maps to the proposal, and the architecture
const MAP = [
  ["Stage 1 — Core chatbot & voice bot (Telugu)", "Farmer Chat: Telugu/English, mic input, spoken replies",
    "దశ 1 — ముఖ్య చాట్‌బాట్ & వాయిస్ బాట్ (తెలుగు)", "రైతు చాట్: తెలుగు/ఇంగ్లీష్, మైక్‌తో మాట్లాడవచ్చు, జవాబులు వినిపిస్తాయి"],
  ["Stage 2 — Publishing Department content", "Content Pipeline: 11-stage ingestion with Contributor / Reviewer / BV roles",
    "దశ 2 — శాఖ సమాచారం ప్రచురణ", "కంటెంట్ పైప్‌లైన్: Contributor / Reviewer / BV పాత్రలతో 11 దశల పరిశీలన"],
  ["Stage 3 — API-based personalised services", "Enter a Farmer ID in chat → application, payment and grievance status",
    "దశ 3 — API ద్వారా మీకు తగిన సేవలు", "చాట్‌లో రైతు ID ఇస్తే → దరఖాస్తు, డబ్బు జమ, ఫిర్యాదుల స్థితి"],
  ["Stage 4 — Deep system integration", "Land & crop records drive tailored advice; Farmer Services screen",
    "దశ 4 — శాఖ వ్యవస్థలతో పూర్తి అనుసంధానం", "భూమి & పంట వివరాల బట్టి సలహాలు; నా వివరాలు స్క్రీన్"],
  ["Channel expansion — Website & WhatsApp", "Channel switch in Farmer Chat (Web / WhatsApp / Voice)",
    "ఛానెళ్ల విస్తరణ — వెబ్‌సైట్ & వాట్సాప్", "రైతు చాట్‌లో ఛానెల్ మార్పు (వెబ్ / వాట్సాప్ / వాయిస్)"],
  ["§2.7 Image-based crop/pest diagnosis", "📷 button in Farmer Chat",
    "§2.7 ఫోటోతో పంట తెగులు/పురుగు గుర్తింపు", "రైతు చాట్‌లో 📷 బటన్"],
  ["§2.9 Governance, testing against agreed scenarios", "Claude vs ChatGPT tab (test runner) and PMU Dashboard",
    "§2.9 పర్యవేక్షణ, ఒప్పుకున్న పరిస్థితులపై పరీక్ష", "Claude vs ChatGPT ట్యాబ్ (పరీక్షలు), PMU డాష్‌బోర్డ్"],
];

export default function About() {
  const { te, t } = useLang();
  return (
    <div className="stack narrow">
      <div className="panel">
        <h2>{t("What is Mock AI mode?", "మాక్ AI మోడ్ అంటే ఏమిటి?")}</h2>
        {te ? (
          <>
            <p>
              ఈ యాప్ రెండు నిజమైన AI మోడళ్లను వాడేలా తయారైంది — <b>Claude</b> (Anthropic) మరియు <b>ChatGPT</b> (OpenAI). వాటిని వాడాలంటే
              డబ్బు కట్టి తీసుకునే API కీలు కావాలి. కీలు వచ్చే వరకు యాప్ <b>మాక్ AI మోడ్</b>‌లో నడుస్తుంది:
            </p>
            <ul>
              <li><b>కీలు అవసరం లేదు, ఇంటర్నెట్ అవసరం లేదు, ఖర్చు లేదు.</b> అంతా మీ ల్యాప్‌టాప్‌లోనే నడుస్తుంది.</li>
              <li>సమాచారం <b>వెతకడం</b> నిజమే: రైతు ఏమి అడుగుతున్నారో (ధర, వాతావరణం, పథకం, పురుగు…) యాప్ గుర్తిస్తుంది, తెలుగా ఇంగ్లీషా గుర్తిస్తుంది, నమూనా సమాచారంలో జవాబు వెతుకుతుంది.</li>
              <li>జవాబు <b>రాయడం</b> అనుకరణ మాత్రమే: AI మోడల్ బదులు ముందే తయారుచేసిన నమూనా వాక్యాలలో వివరాలు నింపుతారు. "Claude (mock)" చుక్కల జాబితాగా, "ChatGPT (mock)" చిన్న సంఖ్యల జాబితాగా రాస్తాయి, అందువల్ల పోలిక స్క్రీన్‌లో తేడా కనిపిస్తుంది.</li>
              <li>సమయం, టోకెన్ల లెక్కలు కూడా <b>అనుకరణ</b> మాత్రమే — డాష్‌బోర్డులు నిజంలా కనిపించడానికి.</li>
              <li>ఫోటోతో తెగులు గుర్తింపు ఫోటోను నిజంగా చూడదు — చిన్న జాబితా నుండి ఒక తెగులును ఎంచుకుంటుంది.</li>
            </ul>
            <h3>తర్వాత నిజమైన AI కి మారడం</h3>
            <ol>
              <li>console.anthropic.com మరియు/లేదా platform.openai.com నుండి API కీ తీసుకోండి.</li>
              <li><code>backend/.env.example</code> ను <code>backend/.env</code> గా కాపీ చేసి, కీలు అందులో పెట్టండి.</li>
              <li>బ్యాకెండ్‌ను మళ్లీ ప్రారంభించండి. పైన ఉన్న గుర్తు ఆకుపచ్చగా ("లైవ్") మారుతుంది. కోడ్ మార్చనవసరం లేదు — అవే వివరాలు నిజమైన మోడల్‌కు వెళ్తాయి; అది జవాబు రాస్తుంది, పంట ఫోటోలను నిజంగా చూడగలదు.</li>
            </ol>
          </>
        ) : (
          <>
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
          </>
        )}
      </div>

      <div className="panel">
        <h2>{t("How the app maps to the proposal", "ప్రతిపాదనలోని ప్రతి భాగం యాప్‌లో ఎక్కడ ఉంది")}</h2>
        <table>
          <thead><tr><th>{t("Proposal", "ప్రతిపాదన")}</th><th>{t("Where in the app", "యాప్‌లో ఎక్కడ")}</th></tr></thead>
          <tbody>
            {MAP.map(([en, enWhere, teText, teWhere]) => (
              <tr key={en}><td>{te ? teText : en}</td><td>{te ? teWhere : enWhere}</td></tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="panel">
        <h2>{t("Architecture", "యాప్ నిర్మాణం")}</h2>
        <pre className="arch">{te ? `React ఫ్రంట్‌ఎండ్ (Vite)
   │  /api/*
FastAPI బ్యాకెండ్ (Python)
   ├── assistant.py  → ప్రశ్నను అర్థం చేసుకుని, వివరాలు వెతుకుతుంది
   ├── ai.py         → Claude / ChatGPT (లైవ్ లేదా మాక్), జవాబు రాస్తుంది
   ├── pipeline.py   → 11 దశల కంటెంట్ పరిశీలన
   └── data.py       → నమూనా రైతులు, పథకాలు, మార్కెట్ ధరలు, వాతావరణం, పురుగులు` : `React frontend (Vite)
   │  /api/*
FastAPI backend (Python)
   ├── assistant.py  → understands the question, fetches facts (retrieval)
   ├── ai.py         → Claude / ChatGPT, live or mock, writes the reply
   ├── pipeline.py   → 11-stage content ingestion
   └── data.py       → dummy farmers, schemes, mandi prices, weather, pests`}</pre>
        <p className="muted">{t("All data is fictional and generated for demonstration only.", "ఇందులోని సమాచారం అంతా కల్పితం — చూపించడానికి మాత్రమే తయారు చేశారు.")}</p>
      </div>
    </div>
  );
}
