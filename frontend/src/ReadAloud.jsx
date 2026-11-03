import { useRef } from "react";
import { useLang } from "./i18n.jsx";
import { speakText, stopSpeaking, useVoice, useVoiceOwner } from "./speech.js";
import VoiceControls from "./VoiceControls.jsx";

// What a block of the page says, as plain text to read aloud: no buttons, form fields or emojis,
// with a pause (full stop) after each box, row and line.
const SKIP = "button, select, textarea, input, label, .no-read, .apply-box, script, style";
const BLOCK = "div, li, p, h1, h2, h3, h4, tr, small, br";
export function textOf(el) {
  const copy = el.cloneNode(true);
  copy.querySelectorAll(SKIP).forEach((n) => n.remove());
  copy.querySelectorAll("[data-say]").forEach((n) => { n.textContent = n.dataset.say; }); // said in words (weather)
  copy.querySelectorAll(BLOCK).forEach((n) => n.after(". "));
  copy.querySelectorAll("b, span, strong, em, a").forEach((n) => n.after(" ")); // "PM-KISAN Approved", not run together
  return copy.textContent
    .replace(/\p{Extended_Pictographic}|️|‍/gu, " ")
    .replace(/·/g, ",")
    .replace(/\s*([.:,])\s*(?:[.,]\s*)+/g, "$1 ")
    .replace(/\s+/g, " ")
    .trim();
}

// 🔊 Read aloud for farmers who find reading hard: reads the block it sits in (the nearest
// [data-read], or its parent), or `text` when given. The floating bar (VoiceBar) has ⏸ / ⏹.
export default function ReadAloud({ text }) {
  const { t, lang } = useLang();
  const ref = useRef(null);
  function read() {
    const box = ref.current.closest("[data-read]") || ref.current.parentElement;
    speakText(text || textOf(box), lang, { owner: "page" });
  }
  return <button ref={ref} className="say-btn read-btn" onClick={read}>🔊 {t("Read aloud", "చదివి వినిపించండి")}</button>;
}

// Floating bar at the bottom while a 🔊 Read aloud on a page is reading
export function VoiceBar() {
  const { t } = useLang();
  const voice = useVoice();
  const owner = useVoiceOwner();
  if (!voice || owner !== "page") return null;
  return (
    <div className="voice-float">
      <b>{voice === "preparing" ? `⏳ ${t("Preparing voice…", "గొంతు సిద్ధమవుతోంది…")}` : `🔊 ${t("Reading aloud…", "చదివి వినిపిస్తోంది…")}`}</b>
      {voice === "preparing"  // ⏹ already while the voice is being made, so it can be cancelled
        ? <button className="voice-icon" onClick={stopSpeaking} title={t("Stop", "ఆపండి")}>⏹</button>
        : <VoiceControls />}
    </div>
  );
}
