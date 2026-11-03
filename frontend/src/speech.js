import { session } from "./api.jsx";

// Read text aloud with a real voice for the language.
// Chrome on Windows has no Telugu voice and reads Telugu letters with an English voice, which
// sounds wrong. So for Telugu: the browser's own Telugu voice if it has one (Edge does), otherwise
// the server's Gemini voice (/api/speak), and the plain browser voice only as a last resort.
let audio = null;
let turn = 0; // goes up on every stop/start, so a voice that arrives after a stop is not played

export function stopSpeaking() {
  turn += 1;
  window.speechSynthesis?.resume(); // Chrome keeps a paused voice paused after cancel(), so the next one would be silent
  window.speechSynthesis?.cancel();
  if (audio) {
    audio.onended = null;
    audio.pause();
    audio = null;
  }
}

// Pause / carry on with what is being read (the Gemini audio or the browser voice)
export function pauseSpeaking() {
  if (audio) audio.pause();
  else window.speechSynthesis?.pause();
}

export function resumeSpeaking() {
  if (audio) audio.play().catch(() => {});
  else window.speechSynthesis?.resume();
}

// The clearest voice the browser has: Telugu needs a real Telugu voice; for English prefer the
// natural-sounding Microsoft "Online (Natural)" and Google voices, Indian English first.
function voiceFor(lang) {
  const voices = window.speechSynthesis?.getVoices() || [];
  if (lang === "te") return voices.find((v) => v.lang?.toLowerCase().startsWith("te"));
  const score = (v) => (/natural|online/i.test(v.name) ? 8 : 0) + (/google/i.test(v.name) ? 6 : 0)
    + (/en[-_]in/i.test(v.lang) ? 3 : 0) + (/female|neerja|aria|jenny|zira|samantha/i.test(v.name) ? 1 : 0);
  return voices.filter((v) => /^en/i.test(v.lang)).sort((a, b) => score(b) - score(a))[0];
}

const clean = (text) => (text || "").replace(/\*\*/g, "").replace(/[•💡➡️📄⚠️🔔✅⏳]/gu, "").trim();

// onReady: the voice is about to start (Gemini audio can take a few seconds to prepare); onEnd: finished
export async function speakText(text, lang, { onReady, onEnd } = {}) {
  stopSpeaking();
  const mine = turn;
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
        const blob = await res.blob();
        if (mine !== turn) return; // stopped (language switched, closed, logged out) while it was being made
        const a = new Audio(URL.createObjectURL(blob));
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
  if (mine !== turn) return;
  onReady?.();
  if (!window.speechSynthesis) return onEnd?.();
  const u = new SpeechSynthesisUtterance(words);
  u.lang = lang === "te" ? "te-IN" : "en-IN";
  if (browserVoice) u.voice = browserVoice;
  u.rate = 0.95; // a little calmer than the default
  u.onend = u.onerror = () => onEnd?.();
  window.rmUtterance = u; // keep a reference: Chrome can drop it before it ends, and then onEnd never runs
  window.speechSynthesis.speak(u);
}
