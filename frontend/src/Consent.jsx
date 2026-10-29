import { useEffect, useState } from "react";
import { api } from "./api.jsx";
import { LangSwitch, useLang } from "./i18n.jsx";
import { speakText, stopSpeaking } from "./speech.js";

// 🔒 Consent: shown once to every farmer before the app. Says what the app keeps and why;
// "I agree" opens the app, "No" logs out with a short message.
export default function Consent({ done, onDecline }) {
  const { te, lang } = useLang();
  const [info, setInfo] = useState(null);
  const [busy, setBusy] = useState(false);
  const [voice, setVoice] = useState(null); // "preparing" | "speaking" | null

  useEffect(() => { api.consentText().then(setInfo).catch(() => {}); }, []);
  useEffect(() => () => stopSpeaking(), []);

  async function answer(agree) {
    setBusy(true);
    stopSpeaking();
    try {
      await api.consentAnswer({ agree, lang });
    } finally {
      setBusy(false);
    }
    if (agree) done();
    else onDecline([info.text.en.declined, info.text.te.declined]);
  }

  function readAloud() {
    if (voice) { stopSpeaking(); setVoice(null); return; } // tap again to stop
    setVoice("preparing");
    speakText(info.speech[lang], lang, { onReady: () => setVoice("speaking"), onEnd: () => setVoice(null) });
  }

  const t = info?.text[lang];
  return (
    <div className="app">
      <div className="sticky-head">
        <header className="topbar">
          <div className="brand">
            <div className="logo">🌾</div>
            <div className="brand-title">{te ? "రైతు మిత్ర" : "Rythu Mitra"}</div>
          </div>
          <div className="status"><LangSwitch className="on-dark" /></div>
        </header>
      </div>
      <main className="content consent-page">
        {t && (
          <div className="panel consent">
            <div className="consent-icon">🔒</div>
            <h2>{t.title}</h2>
            <p>{t.intro}</p>
            <div className="consent-keeps">
              {t.keeps.map(([icon, line]) => <div key={line}><span>{icon}</span>{line}</div>)}
            </div>
            <h3>{t.use_title}</h3>
            <ul>{t.uses.map((u) => <li key={u}>{u}</li>)}</ul>
            <ul className="consent-promise">{t.promise.map((p) => <li key={p}>✔️ {p}</li>)}</ul>
            <small className="muted">{t.law}</small>
            <div className="consent-actions">
              <button onClick={readAloud}>{voice === "preparing" ? (te ? "⏳ గొంతు సిద్ధమవుతోంది…" : "⏳ Preparing voice…")
                : voice === "speaking" ? (te ? "⏹ ఆపండి" : "⏹ Stop") : (te ? "🔊 చదివి వినిపించండి" : "🔊 Read aloud")}</button>
              <button onClick={() => answer(false)} disabled={busy}>✖ {t.decline}</button>
              <button className="primary" onClick={() => answer(true)} disabled={busy}>✅ {t.agree}</button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
