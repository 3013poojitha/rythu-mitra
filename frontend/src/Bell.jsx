import { useEffect, useRef, useState } from "react";
import { api } from "./api.jsx";
import { useLang } from "./i18n.jsx";
import * as fu from "./pages/followup.js";

// 🔔 Notification bell (farmers): asks about remedies Crop Doctor gave - did you use it, when,
// did it work, then a photo of the medicine used and of the crop now. Every answer is saved to My history.
export default function Bell({ refresh }) {
  const { t } = useLang();
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState([]);
  const [done, setDone] = useState([]); // ids answered while the panel is open
  const boxRef = useRef(null);

  const load = () => api.history().then((h) => setPending(h.records.filter((r) => !r.feedback).reverse())).catch(() => {});
  useEffect(() => { load(); }, [refresh]);
  useEffect(() => {
    if (!open) return;
    const close = (e) => { if (!boxRef.current?.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  const waiting = pending.filter((r) => !done.includes(r.id));
  return (
    <div className="bell" ref={boxRef}>
      <button className="bell-btn" title={t("Notifications", "నోటిఫికేషన్లు")}
              onClick={() => { if (!open) { load(); setDone([]); } setOpen(!open); }}>
        🔔{waiting.length > 0 && <span className="bell-count">{waiting.length}</span>}
      </button>
      {open && (
        <div className="bell-panel">
          <div className="bell-head">
            <b>🔔 {t("Notifications", "నోటిఫికేషన్లు")}</b>
            <button className="link" onClick={() => setOpen(false)}>✕</button>
          </div>
          {!pending.length && <p className="muted bell-empty">{t("No new notifications.", "కొత్త నోటిఫికేషన్లు ఏవీ లేవు.")}</p>}
          {pending.map((r) => (
            <RemedyQuestions key={r.id} rec={r} onSaved={() => setDone((d) => [...d, r.id])} />
          ))}
        </div>
      )}
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
    <div className={`bell-item ${state === "saved" ? "saved" : ""}`}>
      <div className="bell-intro">{fu.intro(rec, te, tc, tm).split("\n").map((l, i) => <div key={i}>{bold(l)}</div>)}</div>
      {q && (
        <>
          <b className="bell-q">{q.question}</b>
          <div className="fu-replies">
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
