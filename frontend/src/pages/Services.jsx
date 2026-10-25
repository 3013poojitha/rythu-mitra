import { useEffect, useState } from "react";
import { api } from "../api.jsx";

const statusColor = (s) => (s === "Credited" || s === "Approved" || s === "Resolved" ? "green" : s.startsWith("Rejected") || s === "Escalated" ? "red" : "amber");

export default function Services({ user }) {
  const isFarmer = user.role === "farmer";
  const [farmers, setFarmers] = useState([]);
  const [filter, setFilter] = useState("");
  const [id, setId] = useState(user.farmer_id || "TS1001");
  const [farmer, setFarmer] = useState(null);
  const [cats, setCats] = useState([]);
  const [form, setForm] = useState({ category: "", description: "" });
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.farmers().then(setFarmers);
    api.reference().then((r) => {
      setCats(r.grievance_categories);
      setForm((f) => ({ ...f, category: r.grievance_categories[0] }));
    });
  }, []);
  useEffect(() => {
    setMsg("");
    api.farmer(id).then(setFarmer).catch(() => setFarmer(null));
  }, [id]);

  async function submitGrievance() {
    if (!form.description.trim()) return setMsg("Please describe the problem.");
    const g = await api.createGrievance({ farmer_id: id, ...form });
    setMsg(`Grievance registered. Tracking ID: ${g.grievance_id}`);
    setForm((f) => ({ ...f, description: "" }));
    setFarmer(await api.farmer(id));
  }

  const shown = farmers.filter((f) => `${f.farmer_id} ${f.name} ${f.district}`.toLowerCase().includes(filter.toLowerCase()));

  return (
    <div className={isFarmer ? "" : "svc-layout"}>
      <aside className="panel doc-list" hidden={isFarmer}>
        <input placeholder="Search farmer, ID or district" value={filter} onChange={(e) => setFilter(e.target.value)} />
        {shown.map((f) => (
          <div key={f.farmer_id} className={`doc-item ${f.farmer_id === id ? "sel" : ""}`} onClick={() => setId(f.farmer_id)}>
            <div className="doc-title">{f.name}</div>
            <small className="muted">{f.farmer_id} · {f.district} · {f.total_acres} ac</small>
          </div>
        ))}
      </aside>

      {farmer && (
        <div className="stack">
          <div className="panel">
            <div className="row between wrap">
              <div>
                <h2>{farmer.name}</h2>
                <p className="muted">{farmer.farmer_id} · {farmer.village}, {farmer.district} ({farmer.district_te}) · Age {farmer.age} · {farmer.gender} · Mobile {farmer.mobile.slice(0, 2)}xxxxxx{farmer.mobile.slice(-2)} · {farmer.bank}</p>
              </div>
              <span className="pill green">Consent given for data sharing (demo)</span>
            </div>
            <p className="muted small">This screen shows what the chatbot can see through State APIs (Stage 3) and land/crop records (Stage 4) once a farmer logs in.</p>
          </div>

          <div className="grid2">
            <div className="panel">
              <h3>📋 Scheme applications <span className="tag stage">Stage 3 API</span></h3>
              <table><thead><tr><th>Scheme</th><th>App ID</th><th>Status</th><th>Amount</th></tr></thead>
                <tbody>{farmer.applications.map((a) => (
                  <tr key={a.app_id}><td>{a.scheme}</td><td>{a.app_id}</td><td><span className={`pill ${statusColor(a.status)}`}>{a.status}</span></td><td>{a.amount ? `₹${a.amount.toLocaleString("en-IN")}` : "—"}</td></tr>
                ))}</tbody>
              </table>
            </div>
            <div className="panel">
              <h3>🗺️ Land & crop records <span className="tag stage">Stage 4</span></h3>
              <table><thead><tr><th>Survey no.</th><th>Acres</th><th>Soil</th><th>Water</th><th>Crop</th></tr></thead>
                <tbody>{farmer.plots.map((p) => (
                  <tr key={p.survey_no}><td>{p.survey_no}</td><td>{p.area_acres}</td><td>{p.soil}</td><td>{p.irrigation}</td><td>{p.crop}</td></tr>
                ))}</tbody>
              </table>
            </div>
          </div>

          <div className="grid2">
            <div className="panel">
              <h3>🌦️ Weather — {farmer.district}</h3>
              <div className="weather">
                {farmer.weather.map((w) => (
                  <div key={w.date} className="wday">
                    <small>{new Date(w.date).toLocaleDateString("en-IN", { weekday: "short", day: "numeric" })}</small>
                    <div className="wicon">{w.rain_mm ? (w.condition === "Thunderstorm" ? "⛈️" : "🌧️") : w.condition === "Sunny" ? "☀️" : "⛅"}</div>
                    <b>{w.max_c}°</b><small>{w.min_c}°</small>
                    {w.rain_mm > 0 && <small className="rain">{w.rain_mm}mm</small>}
                  </div>
                ))}
              </div>
              <h3>🌱 Personalised advisory</h3>
              {Object.entries(farmer.advisories).map(([crop, a]) => (
                <div key={crop}><b>{crop}</b><ul>{a.en.slice(0, 3).map((l) => <li key={l}>{l}</li>)}</ul></div>
              ))}
            </div>
            <div className="panel">
              <h3>📣 Grievances <span className="tag stage">Stage 3 API</span></h3>
              {farmer.grievances.length ? farmer.grievances.map((g) => (
                <div key={g.grievance_id} className="row between griev">
                  <span><b>{g.grievance_id}</b> {g.category}<br /><small className="muted">{g.created_on} · {g.channel}</small></span>
                  <span className={`pill ${statusColor(g.status)}`}>{g.status}</span>
                </div>
              )) : <p className="muted">No grievances filed.</p>}
              <h4>Raise a new grievance</h4>
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                {cats.map((c) => <option key={c}>{c}</option>)}
              </select>
              <textarea rows={3} placeholder="Describe the problem" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              <button className="primary" onClick={submitGrievance}>Submit grievance</button>
              {msg && <div className="success">{msg}</div>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
