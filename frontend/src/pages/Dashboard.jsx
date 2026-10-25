import { useEffect, useState } from "react";
import { api } from "../api.jsx";

const INTENT_LABEL = {
  mandi_price: "Mandi prices", weather: "Weather", scheme_info: "Scheme info", crop_advisory: "Crop advisory",
  application_status: "Application status", benefit_status: "Benefit status", grievance: "Grievances",
  pest_diagnosis: "Pest diagnosis", land_records: "Land records", state_content: "State circulars",
  greeting: "Greetings", fallback: "Unanswered",
};
const STATUS = { Done: "green", "In progress": "amber", Blocked: "red", "Not started": "grey", Open: "red", Closed: "green" };

export default function Dashboard() {
  const [d, setD] = useState(null);
  useEffect(() => {
    api.dashboard().then(setD);
  }, []);
  if (!d) return <div className="panel">Loading…</div>;
  const k = d.kpis;
  const maxDay = Math.max(...d.by_day.map((x) => x.count));

  const stageProgress = ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Channels"].map((s) => {
    const items = d.tracker.filter((t) => t.stage === s);
    const score = items.reduce((a, t) => a + (t.status === "Done" ? 1 : t.status === "In progress" ? 0.5 : 0), 0);
    return { stage: s, pct: Math.round((100 * score) / items.length) };
  });

  return (
    <div className="stack">
      <div className="kpis">
        <Kpi label="Farmer queries (30 days)" value={k.total_queries.toLocaleString("en-IN")} />
        <Kpi label="Queries last 7 days" value={k.queries_7d.toLocaleString("en-IN")} />
        <Kpi label="Asked in Telugu" value={`${k.telugu_share}%`} />
        <Kpi label="Helpful answers" value={`${k.helpful_rate}%`} />
        <Kpi label="State docs published" value={`${k.docs_published} / ${k.docs_in_pipeline}`} />
        <Kpi label="Open grievances" value={k.open_grievances} />
      </div>

      <div className="panel">
        <h3>Daily queries</h3>
        <div className="bars-v">
          {d.by_day.map((x) => (
            <div key={x.date} className="barv" title={`${x.date}: ${x.count}`}>
              <div style={{ height: `${(x.count / maxDay) * 100}%` }} />
            </div>
          ))}
        </div>
        <div className="row between"><small className="muted">{d.by_day[0]?.date}</small><small className="muted">{d.by_day.at(-1)?.date}</small></div>
      </div>

      <div className="grid3">
        <Bars title="Top topics" rows={d.by_intent.map(([i, c]) => [INTENT_LABEL[i] || i, c])} />
        <Bars title="By channel" rows={d.by_channel} />
        <Bars title="By district" rows={d.by_district} />
      </div>

      <div className="panel">
        <h3>Integration progress by stage</h3>
        <div className="stage-progress">
          {stageProgress.map((s) => (
            <div key={s.stage}>
              <div className="row between"><b>{s.stage}</b><span>{s.pct}%</span></div>
              <div className="progress big"><div style={{ width: `${s.pct}%` }} /></div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid2">
        <div className="panel">
          <h3>Integration tracker</h3>
          <table><thead><tr><th>Stage</th><th>Item</th><th>Owner</th><th>Due</th><th>Status</th></tr></thead>
            <tbody>{d.tracker.map((t) => (
              <tr key={t.id}><td>{t.stage}</td><td>{t.item}</td><td>{t.owner}</td><td>{t.due}</td><td><span className={`pill ${STATUS[t.status]}`}>{t.status}</span></td></tr>
            ))}</tbody>
          </table>
        </div>
        <div className="panel">
          <h3>Issues, risks & actions register</h3>
          <table><thead><tr><th>ID</th><th>Type</th><th>Title</th><th>Severity</th><th>Status</th></tr></thead>
            <tbody>{d.issues.map((t) => (
              <tr key={t.id}><td>{t.id}</td><td>{t.type}</td><td>{t.title}<br /><small className="muted">{t.owner}</small></td>
                <td><span className={`pill ${t.severity === "High" ? "red" : t.severity === "Medium" ? "amber" : "grey"}`}>{t.severity}</span></td>
                <td><span className={`pill ${STATUS[t.status] || "amber"}`}>{t.status}</span></td></tr>
            ))}</tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Kpi({ label, value }) {
  return <div className="kpi"><b>{value}</b><small>{label}</small></div>;
}

function Bars({ title, rows }) {
  const max = Math.max(...rows.map((r) => r[1]));
  return (
    <div className="panel">
      <h3>{title}</h3>
      {rows.slice(0, 8).map(([l, c]) => (
        <div key={l} className="barh">
          <span>{l}</span>
          <div className="track"><div style={{ width: `${(c / max) * 100}%` }} /></div>
          <small>{c.toLocaleString("en-IN")}</small>
        </div>
      ))}
    </div>
  );
}
