import { session } from "./api.jsx";

// Read text aloud with a real voice for the language.
// Chrome on Windows has no Telugu voice and reads Telugu letters with an English voice, which
// sounds wrong. So for Telugu: the browser's own Telugu voice if it has one (Edge does), otherwise
// the server's Gemini voice (/api/speak), and the plain browser voice only as a last resort.
let audio = null;

export function stopSpeaking() {
  window.speechSynthesis?.cancel();
  if (audio) {
    audio.onended = null;
    audio.pause();
    audio = null;
  }
}

const voiceFor = (lang) =>
  (window.speechSynthesis?.getVoices() || []).find((v) => v.lang?.toLowerCase().startsWith(lang === "te" ? "te" : "en-in"));

const clean = (text) => (text || "").replace(/\*\*/g, "").replace(/[•💡➡️📄⚠️🔔✅⏳]/gu, "").trim();

// onReady: the voice is about to start (Gemini audio can take a few seconds to prepare); onEnd: finished
export async function speakText(text, lang, { onReady, onEnd } = {}) {
  stopSpeaking();
  const words = clean(text);
  const browserVoice = voiceFor(lang);
  if (lang === "te" && !browserVoice) {
    try {
      const token = session.get();
      const res = await fetch("/api/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ text: words, lang }),
      });
      if (res.status === 200) {
        const a = new Audio(URL.createObjectURL(await res.blob()));
        audio = a;
        a.onended = a.onerror = () => { if (audio === a) audio = null; onEnd?.(); };
        onReady?.();
        await a.play();
        return;
      }
    } catch {
      /* no Gemini voice - fall back to the browser below */
    }
  }
  onReady?.();
  if (!window.speechSynthesis) return onEnd?.();
  const u = new SpeechSynthesisUtterance(words);
  u.lang = lang === "te" ? "te-IN" : "en-IN";
  if (browserVoice) u.voice = browserVoice;
  u.onend = u.onerror = () => onEnd?.();
  window.rmUtterance = u; // keep a reference: Chrome can drop it before it ends, and then onEnd never runs
  window.speechSynthesis.speak(u);
}
