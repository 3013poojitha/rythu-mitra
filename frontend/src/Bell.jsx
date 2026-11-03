import ReadAloud from "./ReadAloud.jsx";
import { useEffect, useRef, useState } from "react";
import { api } from "./api.jsx";
import { useLang } from "./i18n.jsx";
import * as fu from "./pages/followup.js";

// 🔔 Notification bell (farmers): spray reminders (when a remedy has to be used again), then questions
// about remedies Crop Doctor gave - did you use it, when, did it work, then a photo of the medicine used
// and of the crop now. Every answer is saved to My history.
export default function Bell({ refresh }) {
  const { t } = useLang();
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState([]);
  const [done, setDone] = useState([]); // ids answered while the panel is open
  const [rems, setRems] = useState([]); // spray reminders (backend/app/reminders.py)
  const [note, setNote] = useState(null); // [en, te] after "I sprayed" / "No more reminders"
  const boxRef = useRef(null);

  const load = () => {
    api.history().then((h) => setPending(h.records.filter((r) => !r.feedback).reverse())).catch(() => {});
    api.reminders().then((r) => setRems(r.reminders)).catch(() => {});
  };
  useEffect(() => { load(); }, [refresh]);
  useEffect(() => {
    if (!open) return;
    const close = (e) => { if (!boxRef.current?.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  const waiting = pending.filter((r) => !done.includes(r.id));
  const count = waiting.length + rems.filter((r) => r.due_now).length; // questions, and sprays due today or late

  async function remAction(r, sprayed) {
    const res = await (sprayed ? api.reminderSprayed(r.id) : api.reminderStop(r.id)).catch(() => null);
    if (!res) return;
    setRems(res.reminders);
    const next = res.reminders.find((x) => x.id === r.id);
    setNote(!sprayed ? ["Okay, no more reminders for this.", "సరే, దీని గురించి ఇక గుర్తు చేయము."]
      : next ? [`Saved. Next one: ${next.en.when}`, `సేవ్ అయింది. తర్వాతది: ${next.te.when}`]
        : ["Saved. That was the last spray for this problem.", "సేవ్ అయింది. ఈ సమస్యకు ఇదే చివరి పిచికారీ."]);
  }
  return (
    <div className="bell" ref={boxRef}>
      <button className="bell-btn" title={t("Notifications", "నోటిఫికేషన్లు")}
              onClick={() => { if (!open) { load(); setDone([]); setNote(null); } setOpen(!open); }}>
        🔔{count > 0 && <span className="bell-count">{count}</span>}
      </button>
      {open && (
        <div className="bell-panel">
          <div className="bell-head">
            <b>🔔 {t("Notifications", "నోటిఫికేషన్లు")}</b>
            <button className="link" onClick={() => setOpen(false)}>✕</button>
          </div>
          {note && <div className="success rem-saved">{t(note[0], note[1])}</div>}
          {!pending.length && !rems.length && <p className="muted bell-empty">{t("No new notifications.", "కొత్త నోటిఫికేషన్లు ఏవీ లేవు.")}</p>}
          {rems.length > 0 && <div className="bell-sub">⏰ {t("Spray reminders", "పిచికారీ గుర్తుచేతలు")}</div>}
          {rems.map((r) => <ReminderCard key={r.id} r={r} onDone={() => remAction(r, true)} onStop={() => remAction(r, false)} />)}
          {rems.length > 0 && pending.length > 0 && <div className="bell-sub">📝 {t("Tell us how the remedy worked", "మందు ఎలా పనిచేసిందో చెప్పండి")}</div>}
          {pending.map((r) => (
            <RemedyQuestions key={r.id} rec={r} onSaved={() => setDone((d) => [...d, r.id])} />
          ))}
        </div>
      )}
    </div>
  );
}

// One spray reminder: what, when, how much, with 🔊 and "I sprayed" (near the day) / "No more reminders"
function ReminderCard({ r, onDone, onStop }) {
  const { lang, t } = useLang();
  const w = r[lang];
  const tone = r.due_now ? "due" : r.days <= 2 ? "soon" : "";
  return (
    <div className={`bell-item rem-card ${tone}`} data-read>
      <div className="rem-top"><b>{r.lure ? "🪤" : "🔁"} {w.title}</b><span className="rem-when">{w.when}</span></div>
      <div className="rem-what">{w.what}</div>
      <div className="rem-med">💊 {w.medicine}</div>
      {w.dose && <div className="rem-dose">{w.dose}</div>}
      <div className="rem-time">⏰ {w.time}</div>
      <div className="rem-rule">{w.rule}</div>
      {w.notes.map((n) => <div key={n} className="rem-note">{n}</div>)}
      <div className="row gap-sm wrap">
        <ReadAloud />
        {r.days <= 2 && <button className="primary" onClick={onDone}>✅ {r.lure ? t("I changed it today", "ఈరోజు ఎర మార్చాను") : t("I sprayed today", "ఈరోజు పిచికారీ చేశాను")}</button>}
        <button onClick={onStop}>{t("No more reminders", "ఇక గుర్తు చేయవద్దు")}</button>
      </div>
    </div>
  );
}

// One remedy: the questions one at a time, then (if it was used) photos of the medicine and the crop now
function RemedyQuestions({ rec, onSaved }) {
  const { te, t, tc, tm, terr } = useLang();
  const [step, setStep] = useState("used");
  const [answers, setAnswers] = useState({});
  const [photos, setPhotos] = useState({}); // {medicine: File, after: File}
  const [state, setState] = useState("asking"); // asking | photo | saving | saved
  const [error, setError] = useState("");
  const q = state === "asking" ? fu.step(step, rec, te, tm) : null;

  function answer(opt) {
    const now = { ...answers, [fu.FIELD[step]]: opt.value };
    setAnswers(now);
    const nextStep = fu.next(step, opt.value, rec);
    if (nextStep) return setStep(nextStep);
    if (now.used === "no") return save(now, null);
    setState("photo"); // used it: ask for photos of the medicine and the crop now
  }

  async function save(body, files) {
    setState("saving");
    setError("");
    try {
      await api.historyFeedback(rec.id, body);
      for (const [kind, file] of Object.entries(files || {})) {
        const form = new FormData();
        form.append("file", file);
        form.append("kind", kind);
        await api.historyPhoto(rec.id, form);
      }
      setState("saved");
      onSaved();
    } catch (e) {
      setError(e.message);
      setState(files ? "photo" : "asking");
    }
  }

  const pick = (kind, icon, label, hint) => (
    <>
      <b className="bell-q">{icon} {label}</b>
      {hint && <small className="muted">{hint}</small>}
      <label className="photo-pick">
        <input type="file" accept="image/*" capture="environment"
               onChange={(e) => setPhotos((p) => ({ ...p, [kind]: e.target.files[0] || undefined }))} />
        {photos[kind] ? `✅ ${photos[kind].name}` : t("📎 Choose or take a photo", "📎 ఫోటో ఎంచుకోండి / తీయండి")}
      </label>
    </>
  );

  const bad = answers.result === "no_change" || answers.result === "worse";
  return (
    <div className={`bell-item ${state === "saved" ? "saved" : ""}`} data-read>
      <ReadAloud />
      {/* 🔊 reads the opening lines only with the first question; after that just this question and its answers */}
      <div className={`bell-intro ${step === "used" ? "" : "no-read"}`}>{fu.intro(rec, te, tc, tm).split("\n").map((l, i) => <div key={i}>{bold(l)}</div>)}</div>
      {q && (
        <>
          <b className="bell-q">{q.question}</b>
          <div className="fu-replies" data-say={q.options.map((o) => o.label).join(", ")}>
            {q.options.map((o) => <button key={`${step}-${o.value}`} onClick={() => answer(o)}>{o.label}</button>)}
          </div>
        </>
      )}
      {state === "photo" && (
        <>
          {pick("medicine", "💊", t("Send a picture of the medicine you used", "మీరు వాడిన మందు ఫోటో పంపండి"),
                t("The bottle or packet, so we can see the name.", "మందు డబ్బా లేదా ప్యాకెట్ — పేరు కనిపించేలా."))}
          {pick("after", "📷", t("Send a photo of your crop now", "ఇప్పుడు మీ పంట ఫోటో పంపండి"),
                t("We keep it next to the first photo, so you can see before and after.", "మొదటి ఫోటో పక్కనే ఉంచుతాం — ముందు, తర్వాత చూడవచ్చు."))}
          <div className="row gap-sm end">
            <button onClick={() => save(answers, null)}>{t("Skip photos", "ఫోటోలు వద్దు")}</button>
            <button className="primary" disabled={!Object.values(photos).some(Boolean)}
                    onClick={() => save(answers, Object.fromEntries(Object.entries(photos).filter(([, f]) => f)))}>{t("Save", "సేవ్ చేయండి")}</button>
          </div>
        </>
      )}
      {state === "saving" && <small className="muted">{t("Saving…", "సేవ్ అవుతోంది…")}</small>}
      {state === "saved" && (
        <div className="success">
          {fu.text.thanks(te).replace(/\*\*/g, "")}
          {bad && <div>{fu.text.sorry(te).replace(/\*\*/g, "")}</div>}
        </div>
      )}
      {error && <div className="error">{terr(error)}</div>}
    </div>
  );
}

const bold = (line) => line.split(/\*\*(.+?)\*\*/g).map((p, j) => (j % 2 ? <strong key={j}>{p}</strong> : p));
