import { useEffect, useState } from "react";
import { api } from "../api.jsx";
import { MONTH_INITIALS, useLang } from "../i18n.jsx";
import { cropIcon } from "./MyFarm.jsx";

// Months are "YYYY-MM" strings
const idx = (m) => { const [y, mm] = m.split("-").map(Number); return y * 12 + mm - 1; };
// Year bands for the timeline axis: [{year, from, to, odd}] in month numbers (to = exclusive)
function yearBands(lo, hi) {
  const out = [];
  for (let y = Math.floor(lo / 12); y <= Math.floor(hi / 12); y++) {
    out.push({ year: y, from: Math.max(y * 12, lo), to: Math.min(y * 12 + 12, hi + 1), odd: y % 2 === 1 });
  }
  return out;
}

// Bar positions in month numbers: a crop fills its months from the start of the sowing
// month to the end of the harvest month. If the next crop on the plot is sown in the
// month the last one was harvested, they share that month half and half.
function barsFor(records, now, lo, hi) {
  const rows = [...records].sort((x, y) => x.start.localeCompare(y.start))
    .map((r) => ({ r, a: idx(r.start), b: idx(r.end || now) + 1 }));
  rows.forEach((cur, i) => {
    const prev = rows[i - 1];
    if (prev && prev.b - 1 === cur.a) prev.b = cur.a = cur.a + 0.5;
  });
  return rows.filter((x) => x.b > lo && x.a < hi + 1)
    .map((x) => ({ ...x, a: Math.max(x.a, lo), b: Math.min(x.b, hi + 1) }));
}

const perAcre = (r) => Math.round((r.yield_qtl / r.area_acres) * 10) / 10;
const SEASON_CLASS = { Kharif: "kharif", Rabi: "rabi", Summer: "summer", Both: "both" };

// Crop history: which crop on which plot, from which month to which month
export default function Seasons({ user, problems }) {
  const { te, t, tv, tc, terr, month: label } = useLang();
  const plotName = (p) => (p === "Other" ? tv("Other") : `${t("Plot")} ${p}`);
  const isFarmer = user.role === "farmer";
  const [farmers, setFarmers] = useState([]);
  const [fid, setFid] = useState(user.farmer_id || "TS1001");
  const [data, setData] = useState(null);
  const [range, setRange] = useState(null);
  const [plot, setPlot] = useState("all");
  const [error, setError] = useState("");

  const load = () => api.seasons(fid).then((d) => {
    setData(d);
    setRange((r) => r || { from: `${Number(d.options.this_month.slice(0, 4)) - 2}-06`, to: d.options.this_month });
  }).catch((e) => setError(e.message));
  useEffect(() => { if (!isFarmer) api.farmers().then(setFarmers); }, []);
  useEffect(() => { setData(null); setPlot("all"); load(); }, [fid]);

  if (error) return <div className="panel error">{terr(error)}</div>;
  if (!data || !range) return <div className="panel">{t("Loading…", "లోడ్ అవుతోంది…")}</div>;

  const now = data.options.this_month;
  const lo = idx(range.from), hi = idx(range.to);
  const inRange = (r) => idx(r.start) <= hi && idx(r.end || now) >= lo;
  const rows = data.records.filter((r) => inRange(r) && (plot === "all" || (r.plot || "Other") === plot));
  const plots = [...new Set(data.records.map((r) => r.plot || "Other"))];
  const span = Math.max(1, hi - lo + 1);
  const pct = (m) => `${((m - lo) / span) * 100}%`;
  const bands = yearBands(lo, hi);
  const problemsFor = (r) => (problems || []).filter((p) => p.farmer_id === fid && p.crop === r.crop &&
    p.created_on.slice(0, 7) >= r.start && p.created_on.slice(0, 7) <= (r.end || now));

  const harvested = rows.filter((r) => !r.growing);
  const totalYield = harvested.reduce((s, r) => s + (r.yield_qtl || 0), 0);

  const nowWord = t("now", "ఇప్పటి వరకు");

  // Group the list by the year the crop was sown
  const groups = [];
  rows.forEach((r) => {
    const y = r.growing ? "now" : r.start.slice(0, 4);
    if (!groups.length || groups[groups.length - 1].y !== y) groups.push({ y, rows: [] });
    groups[groups.length - 1].rows.push(r);
  });

  return (
    <div className="stack">
      <div className="panel">
        <div className="row between wrap">
          <div className="row wrap">
            {!isFarmer && (
              <select className="fit" value={fid} onChange={(e) => setFid(e.target.value)}>
                {farmers.map((f) => <option key={f.farmer_id} value={f.farmer_id}>{f.farmer_id} · {f.name} · {f.district}</option>)}
              </select>
            )}
            <label className="inline">{t("From")} <input type="month" value={range.from} max={range.to} onChange={(e) => e.target.value && setRange({ ...range, from: e.target.value })} /></label>
            <label className="inline">{t("To")} <input type="month" value={range.to} min={range.from} max={now} onChange={(e) => e.target.value && setRange({ ...range, to: e.target.value })} /></label>
          </div>
        </div>
        <div className="chips">
          {["all", ...plots].map((p) => <button key={p} className={plot === p ? "on" : ""} onClick={() => setPlot(p)}>{p === "all" ? t("All plots") : plotName(p)}</button>)}
        </div>

        <div className="info-line mt-sm">
          {t("This is a saved record. When you change a crop on 🏠 My Details, it is added here automatically.",
            "ఇది సేవ్ అయిన రికార్డు. 🏠 నా వివరాలు లో పంట మార్చినప్పుడు ఇక్కడ దానంతట అదే చేరుతుంది.")}
        </div>

        <div className="farm-stats mt">
          <div className="kpi"><small>{t("Crops in this period", "ఈ కాలంలో పంటలు")}</small><b>{rows.length}</b></div>
          <div className="kpi"><small>{t("Growing now")}</small><b>{rows.filter((r) => r.growing).length}</b></div>
          <div className="kpi"><small>{t("Different crops", "వేర్వేరు పంటలు")}</small><b>{new Set(rows.map((r) => r.crop)).size}</b></div>
          <div className="kpi"><small>{t("Total harvest", "మొత్తం దిగుబడి")}</small><b>{Math.round(totalYield * 10) / 10} <span className="unit">{t("qtl")}</span></b></div>
        </div>

        <h3 className="mt">🗓️ {t("Timeline")}: {label(range.from)} – {label(range.to)}</h3>
        <div className="gantt">
          <div className="g-axis">
            <span className="g-name" />
            <div className="g-track">
              {bands.map((y) => (
                <span key={y.year} className={`g-band ${y.odd ? "odd" : ""}`} style={{ left: pct(y.from), width: `${((y.to - y.from) / span) * 100}%` }}>
                  {y.to - y.from >= 2 ? y.year : ""}
                </span>
              ))}
            </div>
          </div>
          {span <= 48 && (
            <div className="g-axis g-months">
              <span className="g-name" />
              <div className="g-track">
                {Array.from({ length: span }, (_, k) => (
                  <span key={k} style={{ left: pct(lo + k), width: `${100 / span}%` }}>{MONTH_INITIALS[te ? "te" : "en"][(lo + k) % 12]}</span>
                ))}
              </div>
            </div>
          )}
          {plots.filter((p) => plot === "all" || p === plot).map((p) => (
            <div key={p} className="g-row">
              <span className="g-name">{plotName(p)}</span>
              <div className="g-track">
                {bands.map((y) => <span key={y.year} className={`g-bg ${y.odd ? "odd" : ""}`} style={{ left: pct(y.from), width: `${((y.to - y.from) / span) * 100}%` }} />)}
                {barsFor(data.records.filter((r) => (r.plot || "Other") === p), now, lo, hi).map(({ r, a, b }) => (
                  <div key={r.id} className={`g-bar ${SEASON_CLASS[r.season] || ""} ${r.growing ? "now" : ""}`}
                       style={{ left: pct(a), width: `calc(${((b - a) / span) * 100}% - 2px)` }}
                       title={`${tc(r.crop)} · ${tv(r.season)} · ${label(r.start)} – ${r.end ? label(r.end) : nowWord}`}>
                    {cropIcon(r.crop)} {te ? tc(r.crop) : r.crop.split(" (")[0]}
                  </div>
                ))}
              </div>
            </div>
          ))}
          <div className="g-legend">
            <span><i className="kharif" /> {t("Kharif (monsoon)", "ఖరీఫ్ (వానాకాలం)")}</span><span><i className="rabi" /> {t("Rabi (winter)", "రబీ (చలికాలం)")}</span>
            <span><i className="summer" /> {tv("Summer")}</span><span><i className="both" /> {tv("Both")}</span><span><i className="now" /> {t("Growing now")}</span>
          </div>
        </div>

        {!rows.length && <div className="empty">{t("No crops in this period. Change the months above.", "ఈ కాలంలో పంటలు లేవు. పైన నెలలు మార్చండి.")}</div>}
        {groups.map((g) => (
          <div key={g.y}>
            <h3 className="mt">{g.y === "now" ? `🌱 ${t("Growing now")}` : te ? `📅 ${g.y} లో విత్తినవి` : `📅 Sown in ${g.y}`}</h3>
            {g.rows.map((r) => {
              const probs = problemsFor(r);
              return (
                <div key={r.id} className="season-card">
                  <div className="plot-crop">{cropIcon(r.crop)}</div>
                  <div className="grow">
                    <div className="row between wrap">
                      <b>{tc(r.crop)}{r.plot ? ` · ${plotName(r.plot)}` : ""}</b>
                      <span className={`pill ${r.growing ? "green" : "grey"}`}>{r.growing ? `🌱 ${t("Growing now")}` : `✅ ${t("Harvested")}`}</span>
                    </div>
                    <div className="season-when">
                      <b>{label(r.start)} → {r.end ? label(r.end) : nowWord}</b>
                      {r.growing && r.expected_end && <> · 🧺 {t("harvest expected", "కోత అంచనా")} {label(r.expected_end)}</>} · {r.months} {te ? (r.months === 1 ? "నెల" : "నెలలు") : r.months === 1 ? "month" : "months"} · {tv(r.season)} · {r.area_acres} {t("acres")}
                    </div>
                    <div className="plot-meta">
                      {r.yield_qtl != null && <span>🧺 {te
                        ? `దిగుబడి ${r.yield_qtl} క్వి. (ఎకరానికి ${perAcre(r)} క్వి.)`
                        : `Harvest ${r.yield_qtl} qtl (${perAcre(r)} qtl/acre)`}</span>}
                      {probs.length > 0 && <span>🩺 {te ? `${probs.length} సమస్యలు` : `${probs.length} problem${probs.length > 1 ? "s" : ""}`}: {[...new Set(probs.map((x) => (te ? x.disease_te : x.disease)))].join(", ")}</span>}
                      <span>📝 {tv(r.source)}</span>
                      {r.notes && <span>“{r.notes}”</span>}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
