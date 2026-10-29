import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { api } from "./api.jsx";
import { useLang } from "./i18n.jsx";
import { speakText, stopSpeaking } from "./speech.js";

// 📅 Today's update (farmers): weather, watering, spraying and crop work due today.
// Opens by itself after the first login of the day; the button beside the 🔔 bell opens it again.
export default function TodayUpdate() {
  const { te, lang, t, date } = useLang();
  const [update, setUpdate] = useState(null);
  const [open, setOpen] = useState(false);
  const [voice, setVoice] = useState(null); // "preparing" | "speaking" | null

  useEffect(() => {
    api.today().then((u) => {
      setUpdate(u);
      if (u.show) {
        setOpen(true);
        api.todaySeen().catch(() => {}); // shown today: opens by itself again tomorrow
      }
    }).catch(() => {});
  }, []);

  function show() {
    api.today().then(setUpdate).catch(() => {});
    setOpen(true);
  }

  function close() {
    stopSpeaking();
    setVoice(null);
    setOpen(false);
  }

  function readAloud() {
    if (!update) return;
    if (voice) { stopSpeaking(); setVoice(null); return; } // tap again to stop
    setVoice("preparing");
    speakText(update.speech[lang], lang, { onReady: () => setVoice("speaking"), onEnd: () => setVoice(null) });
  }

  const w = update?.weather;
  return (
    <>
      <button className="bell-btn today-btn" title={t("Today's update", "ఈరోజు సమాచారం")} onClick={show}>
        📅 <span>{t("Today", "ఈరోజు")}</span>
      </button>
      {/* Drawn on the page body, not inside the green header, so it keeps the normal text colours */}
      {open && update && createPortal(
        <div className="modal-bg" onClick={close}>
          <div className="panel modal today" onClick={(e) => e.stopPropagation()}>
            <div className="today-head">
              <h2>🌾 {t("Today on your farm", "ఈరోజు మీ పొలంలో")}</h2>
              <small className="muted">{date(update.date)} · 📍 {te ? update.district_te : update.district}</small>
            </div>

            {w && (
              <div className="today-weather">
                <span className="today-wicon">{w.icon}</span>
                <div>
                  <b>{te ? w.te : w.en}</b>
                  {w.tomorrow_en && <small className="muted">{te ? w.tomorrow_te : w.tomorrow_en}</small>}
                </div>
              </div>
            )}

            <div className="today-lines">
              {update.weather_lines.map((l) => <Line key={l.en} l={l} te={te} />)}
            </div>
            <h3>🌱 {t("Crop work", "పంట పనులు")}</h3>
            <div className="today-lines">
              {update.crop_lines.map((l) => <Line key={l.en} l={l} te={te} />)}
            </div>
            <small className="muted">{t("Crop reminders are demo timings. Check with your AEO before using fertilizer or medicine.",
              "పంట గుర్తుచేతలు డెమో సమయాలు మాత్రమే. ఎరువు లేదా మందు వాడే ముందు మీ AEO ని అడగండి.")}</small>

            <div className="today-actions">
              <button onClick={readAloud}>{voice === "preparing" ? `⏳ ${t("Preparing voice…", "గొంతు సిద్ధమవుతోంది…")}`
                : voice === "speaking" ? `⏹ ${t("Stop", "ఆపండి")}` : `🔊 ${t("Read aloud", "చదివి వినిపించండి")}`}</button>
              <button className="primary" onClick={close} autoFocus>✅ {t("Done", "సరే")}</button>
            </div>
          </div>
        </div>,
        document.body,
      )}
    </>
  );
}

function Line({ l, te }) {
  return (
    <div className={`today-line ${l.tone}`}>
      <span className="today-icon">{l.icon}</span>
      <span>{te ? l.te : l.en}</span>
    </div>
  );
}
