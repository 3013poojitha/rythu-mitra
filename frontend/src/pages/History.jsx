import { useEffect, useState } from "react";
import { api, historyReport } from "../api.jsx";
import { useLang } from "../i18n.jsx";
import Seasons from "./Seasons.jsx";

const RESULT_ICON = { cured: "✅", improved: "👍", no_change: "➖", worse: "👎" };
const RESULT_PILL = { cured: "green", improved: "green", no_change: "amber", worse: "red" };

// "0.6 g per litre · 9.6 g per 16-L tank · 1.4 tanks" -> Telugu (amounts and units stay as on the label)
const doseTe = (s) => s
  .replace(/([\d.]+ \S+) per litre/g, "లీటరుకు $1")
  .replace(/([\d.]+ \S+) per (\d+)-L tank/g, "$2 లీటర్ల ట్యాంకుకు $1")
  .replace(/([\d.]+) tanks?/g, "$1 ట్యాంకులు")
  .replace(/([\d.]+ \S+) per acre/g, "ఎకరానికి $1");

// Farm history, opened from the user menu: crops grown over time, and problems & remedies
export default function History({ user }) {
  const { t, lang, terr } = useLang();
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  // ⬇ Download saves the page as a file; 🖨️ Print opens the print box (which can also save a PDF)
  async function getReport(action) {
    setBusy(action);
    setError("");
    try {
      const page = await historyReport(lang);
      if (action === "download") {
        const a = document.createElement("a");
        a.href = URL.createObjectURL(new Blob([page], { type: "text/html" }));
        a.download = `farm-history-${user.farmer_id || "report"}.html`;
        a.click();
        setTimeout(() => URL.revokeObjectURL(a.href), 2000);
      } else {
        const frame = document.createElement("iframe");
        frame.style.cssText = "position:fixed;right:0;bottom:0;width:0;height:0;border:0";
        frame.srcdoc = page;
        frame.onload = () => { frame.contentWindow.print(); setTimeout(() => frame.remove(), 60000); };
        document.body.appendChild(frame);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy("");
    }
  }
  const isFarmer = user.role === "farmer";
  const [section, setSection] = useState("crops");
  const [problems, setProblems] = useState([]);
  useEffect(() => { api.history().then((d) => setProblems(d.records)).catch(() => {}); }, [section]);

  return (
    <div className="stack">
      {/* One compact header: title + Download / Print on one line, then the section switch */}
      <div className="panel hist-head">
        <div className="row between wrap">
          <h3>📜 {isFarmer ? t("My farm history", "నా పొలం చరిత్ర") : t("Farm history", "పొలం చరిత్ర")}</h3>
          {isFarmer && (
            <div className="row gap-sm wrap hist-actions">
              <button onClick={() => getReport("download")} disabled={!!busy}>⬇️ {t("Download history", "చరిత్ర డౌన్‌లోడ్ చేయండి")}</button>
              <button onClick={() => getReport("print")} disabled={!!busy}>🖨️ {t("Print / Save as PDF", "ప్రింట్ / PDF గా సేవ్ చేయండి")}</button>
            </div>
          )}
        </div>
        {error && <div className="error">{terr(error)}</div>}
        <small className="muted">
          {t("Crops grown on each plot, and every problem found by Crop Doctor with the remedy and how it worked.",
            "ప్రతి భూమి ముక్కలో సాగు చేసిన పంటలు, పంట వైద్యుడు గుర్తించిన సమస్యలు, ఇచ్చిన మందు, అది ఎలా పనిచేసింది.")}
        </small>
        <div className="seg">
          <button className={section === "crops" ? "on" : ""} onClick={() => setSection("crops")}>🌱 {t("Crops grown")}</button>
          <button className={section === "problems" ? "on" : ""} onClick={() => setSection("problems")}>🩺 {t("Problems & remedies")}</button>
        </div>
      </div>
      {section === "crops" ? <Seasons user={user} problems={problems} /> : <Problems user={user} />}
    </div>
  );
}

// Crop health history (read only): disease found -> remedy given -> did the farmer use it -> result,
// with the crop photos before and after. Farmers answer the questions from the 🔔 bell.
function Problems({ user }) {
  const { te, t, tv, tm, tc, terr, month, day, time } = useLang();
  const isFarmer = user.role === "farmer";
  const [data, setData] = useState(null);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");

  const load = () => api.history().then(setData).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  if (error) return <div className="panel error">{terr(error)}</div>;
  if (!data) return <div className="panel">{t("Loading…", "లోడ్ అవుతోంది…")}</div>;

  const s = data.summary;
  const rows = data.records.filter((r) =>
    (filter === "all" || (filter === "pending" ? !r.feedback : !!r.feedback)) &&
    `${r.farmer_id} ${r.farmer_name} ${r.crop} ${r.disease}`.toLowerCase().includes(search.toLowerCase()));
  const groups = [];
  rows.forEach((r) => {
    const m = r.created_on.slice(0, 7);
    if (!groups.length || groups[groups.length - 1].month !== m) groups.push({ month: m, rows: [] });
    groups[groups.length - 1].rows.push(r);
  });

  return (
    <div className="stack">
      <div className="info-line">
        {te ? (
          <>🩺 {isFarmer ? "మీ పంటలలో కనిపించిన సమస్యలు" : "రైతులందరి పంటలలో కనిపించిన సమస్యలు"}, సూచించిన మందు, వాడారో లేదో, అది ఎలా పనిచేసింది.
            {isFarmer && " మందు చల్లిన తర్వాత ఫలితాన్ని పైన 🔔 గంటలో చెప్పండి — ఇది ఇతర రైతులకు కూడా ఉపయోగపడుతుంది."}</>
        ) : (
          <>🩺 {isFarmer ? "Problems found on your crops" : "Problems found for all farmers"}, the remedy suggested, whether it was used, and how it worked.
            {isFarmer && " After you spray, tell us the result from the 🔔 bell at the top — it helps other farmers too."}</>
        )}
      </div>

      <div className="farm-stats">
        <div className="kpi"><small>{t("Problems found", "కనిపించిన సమస్యలు")}</small><b>{s.cases}</b></div>
        <div className="kpi"><small>{t("Waiting for feedback")}</small><b className={s.pending ? "warn" : ""}>{s.pending}</b></div>
        <div className="kpi"><small>{t("Remedy used", "మందు వాడినవి")}</small><b>{s.used}</b><small>{s.not_used} {t("not used", "వాడలేదు")}</small></div>
        <div className="kpi">
          <small>{t("Remedy worked", "మందు పనిచేసినవి")}</small><b>{s.worked_pct == null ? "—" : `${s.worked_pct}%`}</b>
          <small>{te ? `${s.used} లో ${s.worked} తగ్గాయి లేదా మెరుగుపడ్డాయి` : `${s.worked} of ${s.used} cured or improved`}</small>
        </div>
      </div>

      <div className="panel">
        <div className="row between wrap">
          <div className="seg">
            {[["all", t("All", "అన్నీ")], ["pending", `${t("Waiting", "ఎదురుచూస్తున్నవి")} (${s.pending})`], ["done", t("Feedback given", "సమాధానం ఇచ్చినవి")]].map(([k, l]) => (
              <button key={k} className={filter === k ? "on" : ""} onClick={() => setFilter(k)}>{l}</button>
            ))}
          </div>
          {!isFarmer && <input className="hist-search" placeholder="Search farmer, crop or disease" value={search} onChange={(e) => setSearch(e.target.value)} />}
        </div>

        {!rows.length && (
          <div className="empty">
            <div className="big-icon">🌱</div>
            {data.records.length ? t("Nothing here for this filter.", "ఈ ఎంపికలో ఏమీ లేవు.")
              : te ? <>ఇంకా చరిత్ర లేదు. తెగులు సోకిన మొక్కను చూపించడానికి <a onClick={() => (location.hash = "doctor")}>పంట వైద్యుడు</a> వాడండి — ఫలితం ఇక్కడ సేవ్ అవుతుంది.</>
              : <>No history yet. Use <a onClick={() => (location.hash = "doctor")}>Crop Doctor</a> to check a sick plant — the result is saved here.</>}
          </div>
        )}

        {groups.map((g) => (
          <div key={g.month} className="hist-month">
            <h3>📅 {month(g.month, true)}</h3>
            {g.rows.map((r) => (
              <div key={r.id} className={`hist-card ${r.feedback ? "" : "pending"}`}>
                <div className="hist-date"><b>{day(r.created_on)}</b><small>{time(r.created_on)}</small></div>
                <div className="grow">
                  <div className="row between wrap">
                    <div>
                      <b className="hist-title">{tc(r.crop)}{r.plot ? ` · ${t("Plot")} ${r.plot}` : ""} — {te ? r.disease_te : r.disease}</b>
                      {!te && <span className="te">{r.disease_te}</span>}
                      <div className="muted small">
                        {!isFarmer && <>{r.farmer_name} ({r.farmer_id}), {r.district} · </>}
                        {te
                          ? `${tv(r.type)} · నమ్మకం ${Math.round(r.confidence * 100)}% · ${r.acres} ఎకరాలు · ${tv(r.source)} ద్వారా`
                          : `${r.type} · ${Math.round(r.confidence * 100)}% confidence · ${r.acres} ${r.acres === 1 ? "acre" : "acres"} · via ${r.source}`}
                      </div>
                    </div>
                    <Status fb={r.feedback} opts={data.options} />
                  </div>

                  <div className="hist-steps">
                    <div>
                      <b>{t("Disease spotted", "తెగులు కనిపించింది")}</b>
                      <small>{te ? `${tc(r.crop)} లో ${r.disease_te}` : `${r.disease} on ${r.crop}`}</small>
                    </div>
                    <div>
                      <b>{t("Remedy given", "ఇచ్చిన మందు")}</b>
                      {r.remedies.slice(0, 2).map((m) => (
                        <small key={m.product}>
                          {m.kind === "Organic" ? "🌿" : "🧪"} {tm(m.product)}: {te ? `${doseTe(m.dose)} · కొనాల్సింది ${m.total}` : `${m.dose} · buy ${m.total}`}
                        </small>
                      ))}
                    </div>
                    <div>
                      <b>{t("Used?", "వాడారా?")}</b>
                      <small>{r.feedback ? tv(data.options.used[r.feedback.used]) + (r.feedback.product ? ` — ${tm(r.feedback.product)}` : "") + (r.feedback.reason ? ` — ${tv(r.feedback.reason)}` : "") : t("Not told yet", "ఇంకా చెప్పలేదు")}</small>
                      {r.feedback?.applied_on && <small>{te ? `${day(r.feedback.applied_on)} న పిచికారీ చేశారు` : `Sprayed on ${day(r.feedback.applied_on)}`}</small>}
                    </div>
                    <div>
                      <b>{t("Result", "ఫలితం")}</b>
                      <small>{r.feedback?.result ? `${RESULT_ICON[r.feedback.result]} ${tv(data.options.results[r.feedback.result])}` : r.feedback ? "—" : t("Not told yet", "ఇంకా చెప్పలేదు")}</small>
                      {r.feedback?.notes && <small className="hist-note">“{r.feedback.notes}”</small>}
                    </div>
                  </div>

                  <Photos rec={r} />
                  {!r.feedback && isFarmer && (
                    <small className="muted">🔔 {t("Answer the questions about this remedy from the bell at the top.", "ఈ మందు గురించి ప్రశ్నలకు పైన 🔔 గంటలో సమాధానం ఇవ్వండి.")}</small>
                  )}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

function Status({ fb, opts }) {
  const { t, tv } = useLang();
  if (!fb) return <span className="pill amber">⏳ {t("Waiting for feedback")}</span>;
  if (fb.used === "no") return <span className="pill grey">{t("Not used", "వాడలేదు")}</span>;
  return <span className={`pill ${RESULT_PILL[fb.result]}`}>{RESULT_ICON[fb.result]} {tv(opts.results[fb.result])}</span>;
}

// Crop photo when the disease was found, the medicine used, and the crop after the remedy
function Photos({ rec }) {
  const { t, day } = useLang();
  const urls = rec.photo_urls || {};
  if (!urls.before && !urls.medicine && !urls.after) return null;
  const shot = (kind, label) => (
    <figure className="hist-photo">
      {urls[kind] ? <img src={urls[kind]} alt={label} /> : <div className="no-photo">{t("No photo", "ఫోటో లేదు")}</div>}
      <figcaption><b>{label}</b>{rec.photos?.[kind] && <small>{day(rec.photos[kind].on)}</small>}</figcaption>
    </figure>
  );
  return (
    <div className="hist-photos">
      {shot("before", t("Before remedy", "మందుకు ముందు"))}
      {urls.medicine && shot("medicine", t("Medicine used", "వాడిన మందు"))}
      {shot("after", t("After remedy", "మందు తర్వాత"))}
    </div>
  );
}
