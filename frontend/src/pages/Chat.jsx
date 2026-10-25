import { useEffect, useRef, useState } from "react";
import { api, renderText } from "../api.jsx";

const QUICK = {
  en: [
    "What is the price of cotton today?",
    "Will it rain in Warangal this week?",
    "Tell me about Rythu Bharosa",
    "My maize has holes in the leaves, what should I spray?",
    "What is my application status?",
    "When does paddy procurement start?",
  ],
  te: [
    "మిరప ధర ఎంత?",
    "ఖమ్మం లో వాతావరణం ఎలా ఉంది?",
    "రైతు భరోసా పథకం గురించి చెప్పండి",
    "పత్తి పంటకు ఎరువు సలహా",
    "నా దరఖాస్తు స్థితి ఏమిటి?",
    "నా భూమి వివరాలు చూపించండి",
  ],
};

const CHANNELS = ["Web chatbot", "WhatsApp", "Voice bot"];

export default function Chat({ user }) {
  const isFarmer = user.role === "farmer";
  const [provider, setProvider] = useState("claude");
  const [channel, setChannel] = useState("Web chatbot");
  const [farmerId, setFarmerId] = useState(user.farmer_id || "");
  const [farmers, setFarmers] = useState([]);
  const [lang, setLang] = useState("te");
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [messages, setMessages] = useState([
    { role: "bot", text: "నమస్కారం! నేను రైతు మిత్ర 🌾\nNamaskaram! Ask me about mandi prices, weather, schemes, crop advice — in Telugu or English. You can also send a photo of a sick plant." },
  ]);
  const endRef = useRef(null);
  const fileRef = useRef(null);

  useEffect(() => {
    api.farmers().then(setFarmers).catch(() => {});
  }, []);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const farmer = farmers.find((f) => f.farmer_id === farmerId.toUpperCase());

  async function send(text) {
    const msg = (text ?? input).trim();
    if (!msg || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: msg }]);
    setBusy(true);
    try {
      const res = await api.chat({ message: msg, provider, farmer_id: farmerId || null, channel });
      setMessages((m) => [...m, { role: "bot", ...res }]);
      if (channel === "Voice bot") speak(res.text, res.lang);
    } catch (e) {
      setMessages((m) => [...m, { role: "bot", text: `⚠️ ${e.message}`, error: true }]);
    } finally {
      setBusy(false);
    }
  }

  async function sendImage(file) {
    if (!file) return;
    const url = URL.createObjectURL(file);
    setMessages((m) => [...m, { role: "user", image: url, text: "Photo of affected crop" }]);
    setBusy(true);
    const form = new FormData();
    form.append("file", file);
    form.append("provider", provider);
    form.append("lang", lang);
    try {
      const res = await api.diagnose(form);
      const d = res.diagnosis;
      const te = lang === "te";
      const text = te
        ? `**గుర్తింపు: ${d.name}** (${d.crop}) — నమ్మకం ${Math.round(d.confidence * 100)}%\n\nలక్షణాలు: ${d.symptoms}\n\nనివారణ: ${d.remedy}\n\n📋 పూర్తి మందుల ప్రణాళిక, మోతాదు, భద్రత కోసం "Crop Doctor" ట్యాబ్ చూడండి.\n⚠️ మందులు వాడే ముందు మీ AEO ని సంప్రదించండి.`
        : `**Detected: ${d.name}** (${d.crop}) — ${Math.round(d.confidence * 100)}% confidence\n\nSymptoms: ${d.symptoms}\n\nRemedy: ${d.remedy}\n\n📋 Open the "Crop Doctor" tab for the full spray plan, quantities for your acres and safety steps.\n⚠️ Please confirm with your AEO before spraying.`;
      setMessages((m) => [...m, { role: "bot", ...res, text, intent: "pest_diagnosis" }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "bot", text: `⚠️ ${e.message}`, error: true }]);
    } finally {
      setBusy(false);
      fileRef.current.value = "";
    }
  }

  function listen() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return alert("Voice input needs Chrome or Edge.");
    const rec = new SR();
    rec.lang = lang === "te" ? "te-IN" : "en-IN";
    rec.onresult = (e) => send(e.results[0][0].transcript);
    rec.onend = () => setListening(false);
    setListening(true);
    rec.start();
  }

  return (
    <div className="chat-layout">
      <aside className="panel side">
        <h3>Settings</h3>
        <label>AI model</label>
        <div className="seg">
          <button className={provider === "claude" ? "on" : ""} onClick={() => setProvider("claude")}>Claude</button>
          <button className={provider === "gpt" ? "on" : ""} onClick={() => setProvider("gpt")}>ChatGPT</button>
        </div>
        <label>Channel</label>
        <div className="seg">
          {CHANNELS.map((c) => (
            <button key={c} className={channel === c ? "on" : ""} onClick={() => setChannel(c)}>{c.replace(" chatbot", "")}</button>
          ))}
        </div>
        <label>Language</label>
        <div className="seg">
          <button className={lang === "te" ? "on" : ""} onClick={() => setLang("te")}>తెలుగు</button>
          <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>English</button>
        </div>
        <label>{isFarmer ? "Logged in as" : "Farmer ID (staff can test any farmer)"}</label>
        <input list="farmer-ids" value={farmerId} onChange={(e) => setFarmerId(e.target.value)} placeholder="e.g. TS1001 — optional" readOnly={isFarmer} />
        <datalist id="farmer-ids">
          {farmers.map((f) => <option key={f.farmer_id} value={f.farmer_id}>{f.name} · {f.district}</option>)}
        </datalist>
        {farmer && (
          <div className="farmer-chip">
            ✅ {farmer.name}<br /><small>{farmer.village}, {farmer.district} · {farmer.total_acres} acres · {farmer.crops.join(", ")}</small>
          </div>
        )}
        <label>Try asking</label>
        <div className="quick">
          {QUICK[lang].map((q) => <button key={q} onClick={() => send(q)} disabled={busy}>{q}</button>)}
        </div>
      </aside>

      <section className={`phone ${channel === "WhatsApp" ? "wa" : ""}`}>
        <div className="phone-head">
          <div className="avatar">🌾</div>
          <div>
            <b>Rythu Mitra</b>
            <small>{channel === "WhatsApp" ? "Telangana Agriculture Dept · Verified business" : channel === "Voice bot" ? "Voice bot · replies are spoken aloud" : "agri.telangana.gov.in · Chat"}</small>
          </div>
        </div>
        <div className="messages">
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role} ${m.error ? "err" : ""}`}>
              {m.image && <img src={m.image} alt="crop" className="thumb" />}
              <div className="bubble-text">{renderText(m.text)}</div>
              {m.role === "bot" && m.stage && (
                <div className="meta">
                  <span className="tag stage">{m.stage}</span>
                  {m.sources?.map((s) => <span key={s} className="tag">{s}</span>)}
                  <span className="tag model">{m.model} · {m.latency_ms} ms · {m.tokens_out} tokens</span>
                  <button className="link" onClick={() => speak(m.text, m.lang || lang)} title="Read aloud">🔊</button>
                </div>
              )}
              {m.note && <div className="note">{m.note}</div>}
            </div>
          ))}
          {busy && <div className="msg bot typing"><span /><span /><span /></div>}
          <div ref={endRef} />
        </div>
        <div className="composer">
          <button className="icon" title="Send a crop photo for pest diagnosis" onClick={() => fileRef.current.click()} disabled={busy}>📷</button>
          <input ref={fileRef} type="file" accept="image/*" hidden onChange={(e) => sendImage(e.target.files[0])} />
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder={lang === "te" ? "మీ ప్రశ్న టైప్ చేయండి..." : "Type your question..."}
          />
          <button className={`icon ${listening ? "rec" : ""}`} title="Speak" onClick={listen} disabled={busy}>🎤</button>
          <button className="send" onClick={() => send()} disabled={busy || !input.trim()}>➤</button>
        </div>
      </section>
    </div>
  );
}

function speak(text, lang) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text.replace(/\*\*/g, "").replace(/[•💡➡️📄⚠️]/gu, ""));
  u.lang = lang === "te" ? "te-IN" : "en-IN";
  window.speechSynthesis.speak(u);
}
