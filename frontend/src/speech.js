import { useSyncExternalStore } from "react";
import { session } from "./api.jsx";

// Read text aloud with a real voice for the language.
// Chrome on Windows has no Telugu voice and reads Telugu letters with an English voice, which
// sounds wrong. So for Telugu: the browser's own Telugu voice if it has one (Edge does), otherwise
// the server's Gemini voice (/api/speak), and the plain browser voice only as a last resort.
// The Gemini voice comes in short pieces (/api/speak/parts): the first is ready in a few seconds and
// plays while the rest are still being made.
let audio = null;
let turn = 0; // goes up on every stop/start, so a voice that arrives after a stop is not played

// What is being read now, for the ⏸ / ⏹ icons: null | "preparing" | "speaking" | "paused"
let status = null;
let owner = null; // who started it: "page" = a 🔊 Read aloud on a page (the floating bar shows)
const listeners = new Set();
function setStatus(s) {
  status = s;
  listeners.forEach((fn) => fn());
}
const subscribe = (fn) => { listeners.add(fn); return () => listeners.delete(fn); };
export function useVoice() {
  return useSyncExternalStore(subscribe, () => status);
}
export function useVoiceOwner() {
  return useSyncExternalStore(subscribe, () => owner);
}

export function stopSpeaking() {
  turn += 1;
  window.speechSynthesis?.resume(); // Chrome keeps a paused voice paused after cancel(), so the next one would be silent
  window.speechSynthesis?.cancel();
  if (audio) {
    audio.onended = null;
    audio.pause();
    audio = null;
  }
  owner = null;
  setStatus(null);
}

// Pause / carry on with what is being read (the Gemini audio or the browser voice)
export function pauseSpeaking() {
  if (status !== "speaking") return;
  if (audio) audio.pause();
  else window.speechSynthesis?.pause();
  setStatus("paused");
}

export function resumeSpeaking() {
  if (status !== "paused") return;
  if (audio) audio.play().catch(() => {});
  else window.speechSynthesis?.resume();
  setStatus("speaking");
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

function post(path, body) {
  const token = session.get();
  return fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify(body),
  });
}

// The Gemini voice for each piece, asked for all at once; resolves to a blob URL, or null
async function geminiPieces(words, lang) {
  const res = await post("/api/speak/parts", { text: words, lang });
  if (!res.ok) return null;
  const { parts } = await res.json();
  return parts.map((part) => post("/api/speak", { text: part, lang })
    .then((r) => (r.status === 200 ? r.blob() : null))
    .then((b) => (b ? URL.createObjectURL(b) : null))
    .catch(() => null));
}

// onReady: the voice is about to start (Gemini audio can take a few seconds to prepare); onEnd: finished
export async function speakText(text, lang, { onReady, onEnd, owner: by } = {}) {
  stopSpeaking();
  owner = by || null;
  const mine = turn;
  setStatus("preparing");
  const words = clean(text);
  const browserVoice = voiceFor(lang);
  const finish = () => { if (mine === turn) { audio = null; setStatus(null); onEnd?.(); } };
  if (lang === "te" && !browserVoice) {
    try {
      const pieces = await geminiPieces(words, lang);
      const first = pieces && await pieces[0];
      if (first) {
        let started = false;
        for (const piece of pieces) {
          const url = await piece;
          if (mine !== turn) return; // stopped (language switched, closed, logged out) while it was being made
          if (!url) continue; // a piece that could not be voiced: go on with the next
          if (!started) { started = true; setStatus("speaking"); onReady?.(); }
          const a = new Audio(url);
          audio = a;
          await new Promise((done) => { a.onended = a.onerror = done; a.play().catch(done); });
          if (mine !== turn) return;
        }
        return finish();
      }
    } catch {
      /* no Gemini voice - fall back to the browser below */
    }
  }
  if (mine !== turn) return;
  setStatus("speaking");
  onReady?.();
  if (!window.speechSynthesis) return finish();
  const u = new SpeechSynthesisUtterance(words);
  u.lang = lang === "te" ? "te-IN" : "en-IN";
  if (browserVoice) u.voice = browserVoice;
  u.rate = 0.95; // a little calmer than the default
  u.onend = u.onerror = finish;
  window.rmUtterance = u; // keep a reference: Chrome can drop it before it ends, and then onEnd never runs
  window.speechSynthesis.speak(u);
}
