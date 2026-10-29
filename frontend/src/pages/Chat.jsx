import { useEffect, useRef, useState } from "react";
import { api, renderText } from "../api.jsx";
import { useLang } from "../i18n.jsx";
import { speakText, stopSpeaking } from "../speech.js";
import { mediaForm, toItems } from "../MediaPicker.jsx";

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

const WELCOME = {
  en: "Namaskaram! I am Rythu Mitra 🌾\nAsk me about mandi prices, weather, schemes, crop advice — in Telugu or English. You can also send a photo of a sick plant.",
  te: "నమస్కారం! నేను రైతు మిత్ర 🌾\nమార్కెట్ ధరలు, వాతావరణం, పథకాలు, పంట సలహాల గురించి అడగండి — తెలుగులో గానీ ఇంగ్లీష్‌లో గానీ. తెగులు సోకిన మొక్క ఫోటో కూడా పంపవచ్చు.",
};

// Said aloud when the farmer taps the mic: the full welcome the first time, then a short prompt
const VOICE_HELLO = {
  en: "Welcome to Rythu Mitra. You can now talk and ask your question.",
  te: "రైతు మిత్రకు స్వాగతం. ఇప్పుడు మీరు మాట్లాడి మీ ప్రశ్న అడగవచ్చు.",
};
const VOICE_AGAIN = { en: "Please ask your question.", te: "మీ ప్రశ్న అడగండి." };

// Telugu for the stage / source tags the backend puts under each reply
const STAGE_TE = {
  "Stage 1 - Central data": "దశ 1 - కేంద్ర సమాచారం",
  "Stage 2 - State content": "దశ 2 - రాష్ట్ర సమాచారం",
  "Stage 3 - Personalised (login needed)": "దశ 3 - మీ వివరాలు (లాగిన్ కావాలి)",
  "Stage 3 - API-based personalised service": "దశ 3 - మీ వివరాల సేవ",
  "Stage 4 - Deep integration (land & crop data)": "దశ 4 - భూమి & పంట వివరాలు",
};
const SOURCE_TE = {
  "Agmarknet mandi prices (dummy)": "అగ్‌మార్క్‌నెట్ మార్కెట్ ధరలు (నమూనా)",
  "IMD district forecast (dummy)": "IMD జిల్లా వాతావరణ సూచన (నమూనా)",
  "State scheme guidelines (dummy)": "రాష్ట్ర పథకం నియమాలు (నమూనా)",
  "Central scheme guidelines (dummy)": "కేంద్ర పథకం నియమాలు (నమూనా)",
  "Scheme directory (dummy)": "పథకాల జాబితా (నమూనా)",
  "ICAR crop advisory (dummy)": "ICAR పంట సలహా (నమూనా)",
  "Land & crop records (dummy)": "భూమి & పంట రికార్డులు (నమూనా)",
  "Scheme application API (dummy)": "పథకం దరఖాస్తు API (నమూనా)",
  "DBT benefit status API (dummy)": "DBT డబ్బు జమ స్థితి API (నమూనా)",
  "Grievance redressal API (dummy)": "ఫిర్యాదుల పరిష్కారం API (నమూనా)",
  "Bhu Bharathi land records (dummy)": "భూ భారతి భూమి రికార్డులు (నమూనా)",
};
const sourceTe = (s) => SOURCE_TE[s] || s.replace(/^State circular: /, "రాష్ట్ర సర్క్యులర్: ");
const noteTe = (n) => (/^Live call failed/.test(n) ? "లైవ్ AI పనిచేయలేదు; మాక్ జవాబు చూపిస్తున్నాం." : n);

// One chat for typing and talking: type a question, or tap the mic - it welcomes you aloud, listens,
// and reads the answer back. embedded = shown under the farmer's details on My Details.
export default function Chat({ user, waOpen, embedded = false }) {
  const { lang, te, t, tc, td, terr } = useLang();
  const isFarmer = user.role === "farmer";
  const [provider, setProvider] = useState("claude");
  // WhatsApp look is opened from the floating WhatsApp button
  const [channel, setChannel] = useState(waOpen ? "WhatsApp" : "Web chatbot");
  const boxRef = useRef(null);
  useEffect(() => {
    setChannel(waOpen ? "WhatsApp" : "Web chatbot");
    if (waOpen && embedded) boxRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [waOpen]);
  const [farmerId, setFarmerId] = useState(user.farmer_id || "");
  const [farmers, setFarmers] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [voice, setVoice] = useState(null); // null | "greeting" | "listening" | "speaking"
  const greeted = useRef(false);
  const recRef = useRef(null);
  // A message has fixed `text` (replies from the backend), or `make(te)` for our own texts so they
  // follow the language switch, or `err` (an error shown through terr)
  const [messages, setMessages] = useState([{ role: "bot", make: (isTe) => WELCOME[isTe ? "te" : "en"] }]);
  const endRef = useRef(null);
  const fileRef = useRef(null);

  useEffect(() => {
    // Scroll inside the chat box only, so the page itself does not jump
    const box = endRef.current?.parentElement;
    if (box) box.scrollTop = box.scrollHeight;
  }, [messages, busy]);

  useEffect(() => {
    api.farmers().then(setFarmers).catch(() => {});
  }, []);

  // Language switched: redo earlier answers in the new language (not counted again on the dashboard)
  useEffect(() => {
    messages.forEach((msg) => {
      if (!msg.ask || msg.lang === lang) return;
      api.chat({ ...msg.ask, lang, log: false })
        .then((res) => setMessages((all) => all.map((x) => (x === msg ? { ...x, ...res } : x))))
        .catch(() => {});
    });
  }, [lang]);

  const farmer = farmers.find((f) => f.farmer_id === farmerId.toUpperCase());

  // spoken = the question was spoken (shown as a voice note on WhatsApp, otherwise the answer is read aloud)
  async function send(text, spoken = false, audio = null) {
    const msg = (text ?? input).trim();
    if (!msg || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: msg, voice: spoken && channel === "WhatsApp", audio }]);
    setBusy(true);
    try {
      const ask = { message: msg, provider, farmer_id: farmerId || null, channel };
      const res = await api.chat({ ...ask, lang });
      // WhatsApp: a voice note gets a voice-note reply, like a real officer would send
      setMessages((m) => [...m, { role: "bot", ...res, ask, voice: spoken && channel === "WhatsApp" }]);
      if (spoken && channel !== "WhatsApp") talk(res.text, res.lang);
    } catch (e) {
      setMessages((m) => [...m, { role: "bot", err: e.message, error: true }]);
    } finally {
      setBusy(false);
    }
  }

  // Any number of photos and videos of the sick crop, sent together and checked as one case
  async function sendMedia(files) {
    if (!files?.length) return;
    const items = toItems(files);
    const nPhotos = items.filter((x) => !x.video).length, nVideos = items.length - nPhotos;
    setMessages((m) => [...m, { role: "user", media: items, make: (isTe) => isTe
      ? `తెగులు సోకిన పంట — ${nPhotos} ${nPhotos === 1 ? "ఫోటో" : "ఫోటోలు"}${nVideos ? `, ${nVideos} ${nVideos === 1 ? "వీడియో" : "వీడియోలు"}` : ""}`
      : `Affected crop — ${nPhotos} photo${nPhotos === 1 ? "" : "s"}${nVideos ? `, ${nVideos} video${nVideos === 1 ? "" : "s"}` : ""}` }]);
    setBusy(true);
    const form = mediaForm(items);
    form.append("provider", provider);
    form.append("lang", lang);
    form.append("source", "Chat");
    try {
      const res = await api.diagnose(form);
      // Built for both languages, so the reply follows the language switch
      const make = (isTe) => {
        const d = res.both?.[isTe ? "te" : "en"] || res.diagnosis;
        const text = d.status !== "detected" ? `**${d.name}** — ${d.remedy}` : isTe
          ? `**గుర్తింపు: ${d.name}** (${d.crop}) — నమ్మకం ${Math.round(d.confidence * 100)}%\n\nలక్షణాలు: ${d.symptoms}\n\nనివారణ: ${d.remedy}\n\n📋 పూర్తి మందుల ప్రణాళిక, మోతాదు, భద్రత కోసం "పంట వైద్యుడు" ట్యాబ్ చూడండి.\n⚠️ మందులు వాడే ముందు మీ AEO ని సంప్రదించండి.`
          : `**Detected: ${d.name}** (${d.crop}) — ${Math.round(d.confidence * 100)}% confidence\n\nSymptoms: ${d.symptoms}\n\nRemedy: ${d.remedy}\n\n📋 Open the "Crop Doctor" tab for the full spray plan, quantities for your acres and safety steps.\n⚠️ Please confirm with your AEO before spraying.`;
        const saved = !res.history_id ? "" : isTe
          ? "\n📜 మీ చరిత్రలో సేవ్ అయింది. మందు వాడిన తర్వాత పైన 🔔 గంటలో ఫలితం, ఫోటో పంపండి."
          : "\n📜 Saved to your History. After you use the remedy, tell us the result and send a photo from the 🔔 bell at the top.";
        return text + saved;
      };
      const { media: _counts, ...reply } = res; // "media" in the reply is just the photo/video count
      setMessages((m) => [...m, { role: "bot", ...reply, make, intent: "pest_diagnosis" }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "bot", err: e.message, error: true }]);
    } finally {
      setBusy(false);
      fileRef.current.value = "";
    }
  }

  // Mic tapped: say the welcome in the chosen language, then listen
  function micTap() {
    if (voice) return stopVoice();
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return alert(t("Voice input needs Chrome or Edge.", "మాట్లాడి అడగడానికి Chrome లేదా Edge బ్రౌజర్ కావాలి."));
    const first = !greeted.current;
    greeted.current = true;
    if (first) setMessages((m) => [...m, { role: "bot", followup: true, make: (isTe) => VOICE_HELLO[isTe ? "te" : "en"] }]);
    setVoice("greeting");
    speak((first ? VOICE_HELLO : VOICE_AGAIN)[lang], lang, () => listen(SR));
  }

  function stopVoice() {
    stopSpeaking();
    recRef.current?.abort();
    setVoice(null);
  }

  function listen(SR) {
    const rec = new SR();
    recRef.current = rec;
    rec.lang = te ? "te-IN" : "en-IN";
    rec.onresult = (e) => send(e.results[0][0].transcript, true);
    rec.onerror = (e) => setMessages((m) => [...m, { role: "bot", followup: true, make: (isTe) => e.error === "not-allowed"
      ? (isTe ? "మైక్ అనుమతి ఇవ్వండి (బ్రౌజర్ పైభాగంలో), తర్వాత మళ్లీ నొక్కండి." : "Please allow the microphone (top of the browser), then tap again.")
      : (isTe ? "వినలేకపోయాను. మళ్లీ మైక్ నొక్కండి, లేదా ప్రశ్న టైప్ చేయండి." : "Couldn't hear you. Tap the mic again, or type your question.") }]);
    rec.onend = () => setVoice((v) => (v === "listening" ? null : v));
    setVoice("listening");
    rec.start();
  }

  function talk(text, l) {
    setVoice("speaking");
    speak(text, l || lang, () => setVoice((v) => (v === "speaking" ? null : v)));
  }

  // 🎙️ Record a voice message (works in every browser with a microphone)
  const [recording, setRecording] = useState(null); // {rec, started}
  const [recSecs, setRecSecs] = useState(0);
  useEffect(() => {
    if (!recording) return;
    const id = setInterval(() => setRecSecs(Math.round((Date.now() - recording.started) / 1000)), 500);
    return () => clearInterval(id);
  }, [recording]);

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream);
      const chunks = [];
      rec.ondataavailable = (e) => chunks.push(e.data);
      rec.onstop = () => {
        stream.getTracks().forEach((tr) => tr.stop());
        sendRecording(new Blob(chunks, { type: rec.mimeType || "audio/webm" }));
      };
      rec.start();
      setRecSecs(0);
      setRecording({ rec, started: Date.now() });
    } catch {
      setMessages((m) => [...m, { role: "bot", followup: true, make: (isTe) => isTe
        ? "🎙️ మైక్ దొరకలేదు. బ్రౌజర్ పైభాగంలో మైక్ అనుమతి ఇవ్వండి."
        : "🎙️ Couldn't use the microphone. Please allow it at the top of the browser." }]);
    }
  }

  function stopRecording() {
    recording?.rec.stop();
    setRecording(null);
  }

  async function sendRecording(blob) {
    const audio = URL.createObjectURL(blob);
    const form = new FormData();
    form.append("file", blob, "voice.webm");
    form.append("lang", lang);
    setBusy(true);
    try {
      const { text } = await api.transcribe(form);
      setBusy(false);
      if (text) return send(text, true, audio);
    } catch {
      setBusy(false);
    }
    // Mock mode: nothing can turn a recording into words without an AI key
    setMessages((m) => [...m, { role: "user", audio, text: "" }, { role: "bot", followup: true, make: (isTe) => isTe
      ? "🎙️ మీ వాయిస్ మెసేజ్ అందింది. ఈ డెమో (మాక్ AI మోడ్)లో రికార్డింగ్‌ను మాటలుగా మార్చలేము — దానికి AI కీ కావాలి. దయచేసి **మైక్** బటన్ నొక్కి మాట్లాడండి, లేదా ప్రశ్న టైప్ చేయండి."
      : "🎙️ I got your voice message. In this demo (Mock AI mode) a recording can't be turned into words — that needs an AI key. Please tap the **mic** button and speak, or type your question." }]);
  }

  const RecordButton = () => recording
    ? <button className="rec-btn on" onClick={stopRecording}>⏹ {t("Stop & send", "ఆపి పంపండి")} · 0:{String(recSecs).padStart(2, "0")}</button>
    : <button className="rec-btn" onClick={startRecording} disabled={busy}>🎙️ {t("Record a voice message", "వాయిస్ మెసేజ్ రికార్డ్ చేయండి")}</button>;

  const textOf = (m) => (m.make ? m.make(te, tc) : m.err != null ? `⚠️ ${terr(m.err)}` : m.text);

  return (
    <div className={embedded ? "chat-embedded" : "chat-layout"} ref={boxRef}>
      {embedded ? (
        null
      ) : (
      <aside className="panel side">
        <h3>{t("Settings", "అమరికలు")}</h3>
        <label>{t("AI model", "AI మోడల్")}</label>
        <div className="seg">
          <button className={provider === "claude" ? "on" : ""} onClick={() => setProvider("claude")}>Claude</button>
          <button className={provider === "gpt" ? "on" : ""} onClick={() => setProvider("gpt")}>ChatGPT</button>
                <button className={provider === "gemini" ? "on" : ""} onClick={() => setProvider("gemini")}>Gemini</button>
        </div>
        <label>{isFarmer ? t("Logged in as", "లాగిన్ అయినవారు") : t("Farmer ID (staff can test any farmer)", "రైతు ID (సిబ్బంది ఏ రైతునైనా పరీక్షించవచ్చు)")}</label>
        <input list="farmer-ids" value={farmerId} onChange={(e) => setFarmerId(e.target.value)} placeholder={t("e.g. TS1001 — optional", "ఉదా. TS1001 (అవసరమైతే)")} readOnly={isFarmer} />
        <datalist id="farmer-ids">
          {farmers.map((f) => <option key={f.farmer_id} value={f.farmer_id}>{f.name} · {f.district}</option>)}
        </datalist>
        {farmer && (
          <div className="farmer-chip">
            ✅ {farmer.name}<br /><small>{farmer.village}, {td(farmer.district)} · {farmer.total_acres} {t("acres")} · {farmer.crops.map(tc).join(", ")}</small>
          </div>
        )}
        <label>{t("Try asking", "ఇలా అడగండి")}</label>
        <div className="quick">
          {QUICK[lang].map((q) => <button key={q} onClick={() => send(q)} disabled={busy}>{q}</button>)}
        </div>
      </aside>
      )}

      <section className={`phone ${channel === "WhatsApp" ? "wa" : ""}`}>
        <div className="phone-head">
          <div className="avatar">🌾</div>
          <div>
            {/* The farmer's chat on Home says "Ask Rythu Mitra" right in its green header */}
            <b>{embedded ? t("Ask Rythu Mitra", "రైతు మిత్రను అడగండి") : t("Rythu Mitra")}</b>
            <small>{channel === "WhatsApp" ? t("Telangana Agriculture Dept · Verified business", "తెలంగాణ వ్యవసాయ శాఖ · ధృవీకరించిన ఖాతా")
              : t("Type or tap the mic to talk", "టైప్ చేయండి లేదా మైక్ నొక్కి మాట్లాడండి")}</small>
          </div>
        </div>
        <div className="messages">
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role} ${m.error ? "err" : ""} ${m.followup ? "fu" : ""}`}>
              {m.image && <img src={m.image} alt="crop" className="thumb" />}
              {Array.isArray(m.media) && (
                <div className="msg-media">
                  {m.media.map((x) => (x.video
                    ? <video key={x.url} src={x.url} controls playsInline />
                    : <img key={x.url} src={x.url} alt="crop" />))}
                </div>
              )}
              {m.audio && <audio controls src={m.audio} className="vm-audio" />}
              {m.voice && !m.audio && <VoiceNote text={textOf(m)} onPlay={() => talk(textOf(m), m.lang)} mine={m.role === "user"} />}
              <div className={`bubble-text ${m.voice ? "transcript" : ""}`}>{renderText(textOf(m))}</div>
              {m.role === "bot" && m.stage && (
                <div className="meta">
                  <span className="tag stage">{te ? STAGE_TE[m.stage] || m.stage : m.stage}</span>
                  {m.sources?.map((s) => <span key={s} className="tag">{te ? sourceTe(s) : s}</span>)}
                  <span className="tag model">{m.model} · {m.latency_ms} ms · {m.tokens_out} {t("tokens", "టోకెన్లు")}</span>
                  <button className="link" onClick={() => speak(m.text, m.lang || lang)} title={t("Read aloud", "చదివి వినిపించండి")}>🔊</button>
                </div>
              )}
              {m.note && <div className="note">{te ? noteTe(m.note) : m.note}</div>}
            </div>
          )).flatMap((el, i) => (embedded && i === 0 ? [el,
            // Suggested questions inside the chat, under the welcome: tap one to ask it
            <div key="quick" className="quick inline in-chat">
              {QUICK[lang].map((q) => <button key={q} onClick={() => send(q)} disabled={busy}>{q}</button>)}
            </div>] : [el]))}
          {busy && <div className="msg bot typing"><span /><span /><span /></div>}
          <div ref={endRef} />
        </div>
        {voice && (
          <div className="voice-bar">
            <span className={`dot ${voice}`} />
            <b>{voice === "greeting" ? t("Rythu Mitra is speaking…", "రైతు మిత్ర మాట్లాడుతోంది…")
              : voice === "listening" ? t("Listening… speak now", "వింటున్నాను… ఇప్పుడు మాట్లాడండి")
              : t("Reading the answer…", "జవాబు చదువుతున్నాను…")}</b>
            <button onClick={stopVoice}>⏹ {t("Stop", "ఆపండి")}</button>
          </div>
        )}
        <div className="composer">
          <button className="icon" title={t("Send crop photos or videos (as many as you like)", "పంట ఫోటోలు / వీడియోలు పంపండి (ఎన్నైనా)")} onClick={() => fileRef.current.click()} disabled={busy}>📷</button>
          <input ref={fileRef} type="file" accept="image/*,video/*" multiple hidden onChange={(e) => { sendMedia(e.target.files); e.target.value = ""; }} />
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder={te ? "మీ ప్రశ్న టైప్ చేయండి లేదా మైక్ నొక్కండి..." : "Type your question or tap the mic..."}
          />
          <button className={`icon mic ${voice === "listening" ? "rec" : ""}`} title={t("Tap and speak", "నొక్కి మాట్లాడండి")} onClick={micTap} disabled={busy && !voice}><MicIcon /></button>
          <button className="send" onClick={() => send()} disabled={busy || !input.trim()}>➤</button>
        </div>
        {channel === "WhatsApp" && <div className="wa-rec"><RecordButton /></div>}
      </section>
    </div>
  );
}

// Read aloud with a real voice for the language (see speech.js)
function speak(text, lang, onEnd) {
  speakText(text, lang, { onEnd });
}

// WhatsApp-style voice note: play button, sound bars and length (about 2.5 words a second)
function VoiceNote({ text, onPlay, mine }) {
  const secs = Math.max(2, Math.round(text.split(/\s+/).length / 2.5));
  return (
    <div className={`voice-note ${mine ? "mine" : ""}`}>
      <button onClick={onPlay} aria-label="Play">▶</button>
      <span className="bars">{Array.from({ length: 22 }, (_, i) => <i key={i} style={{ height: `${4 + ((i * 7 + secs * 3) % 13)}px` }} />)}</span>
      <small>{Math.floor(secs / 60)}:{String(secs % 60).padStart(2, "0")}</small>
    </div>
  );
}

// Microphone icon (like WhatsApp's) for the talk button; takes the button's text colour
function MicIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
      <path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2z" />
    </svg>
  );
}
