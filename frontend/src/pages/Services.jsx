import { useEffect, useState } from "react";
import { api } from "../api.jsx";
import { useLang } from "../i18n.jsx";
import MyFarm from "./MyFarm.jsx";
import Chat from "./Chat.jsx";

const statusColor = (s) => (s === "Credited" || s === "Approved" || s === "Resolved" ? "green" : s.startsWith("Rejected") || s === "Escalated" ? "red" : "amber");

export default function Services({ user, refreshUser, waOpen }) {
  const { te, t, tv, tc, date, weekday } = useLang();
  const isFarmer = user.role === "farmer";
  const [farmers, setFarmers] = useState([]);
  const [filter, setFilter] = useState("");
  const [id, setId] = useState(user.farmer_id || "TS1001");
  const [farmer, setFarmer] = useState(null);
  const [cats, setCats] = useState([]);
  const [form, setForm] = useState({ category: "", description: "" });
  const [msg, setMsg] = useState(null); // [English, Telugu]

  useEffect(() => {
    api.farmers().then(setFarmers);
    api.reference().then((r) => {
      setCats(r.grievance_categories);
      setForm((f) => ({ ...f, category: r.grievance_categories[0] }));
    });
  }, []);
  useEffect(() => {
    setMsg(null);
    api.farmer(id).then(setFarmer).catch(() => setFarmer(null));
  }, [id]);

  async function submitGrievance() {
    if (!form.description.trim()) return setMsg(["Please describe the problem.", "దయచేసి సమస్య ఏమిటో రాయండి."]);
    const g = await api.createGrievance({ farmer_id: id, ...form });
    setMsg([`Grievance registered. Tracking ID: ${g.grievance_id}`, `ఫిర్యాదు నమోదైంది. ట్రాకింగ్ ID: ${g.grievance_id}`]);
    setForm((f) => ({ ...f, description: "" }));
    setFarmer(await api.farmer(id));
  }

  // Staff-only farmer list stays in English
  const shown = farmers.filter((f) => `${f.farmer_id} ${f.name} ${f.district}`.toLowerCase().includes(filter.toLowerCase()));

  return (
    <div className={isFarmer ? "" : "svc-layout"}>
      {!isFarmer && (
        <aside className="panel doc-list">
          <input placeholder="Search farmer, ID or district" value={filter} onChange={(e) => setFilter(e.target.value)} />
          {shown.map((f) => (
            <div key={f.farmer_id} className={`doc-item ${f.farmer_id === id ? "sel" : ""}`} onClick={() => setId(f.farmer_id)}>
              <div className="doc-title">{f.name}</div>
              <small className="muted">{f.farmer_id} · {f.district} · {f.total_acres} ac</small>
            </div>
          ))}
        </aside>
      )}

      {farmer && (
        <div className="svc-two">
          <div className="stack">
            <MyFarm farmer={farmer} isFarmer={isFarmer}
                    onSaved={(f) => { setFarmer(f); api.farmers().then(setFarmers); refreshUser?.(); }} />
            {/* Farmers ask questions right here: type, or tap 🎤 and talk */}
            {isFarmer && <div className="panel"><Chat user={user} waOpen={waOpen} embedded /></div>}
          </div>

          {/* Right side: tap a row to open what it contains */}
          <aside className="svc-side">
            <Section icon="📋" title={t("Scheme applications")} hint={farmer.applications.length}>
              {farmer.applications.map((a) => (
                <div key={a.app_id} className="side-row">
                  <span className="grow"><b>{te && a.scheme_te ? a.scheme_te : a.scheme}</b><small className="muted">{a.app_id}</small></span>
                  <span className="pay-amt">
                    <span className={`pill ${statusColor(a.status)}`}>{tv(a.status)}</span>
                    <small>{a.amount ? rupees(a.amount) : "—"}</small>
                  </span>
                </div>
              ))}
            </Section>

            <Section icon="💰" title={t("Payment status", "డబ్బు జమ స్థితి")}
                     hint={rupees(farmer.applications.filter((a) => a.status === "Credited").reduce((n, a) => n + a.amount, 0))}>
              <Payments farmer={farmer} />
            </Section>

            <Section icon="📣" title={t("Grievances")}
                     hint={`${farmer.grievances.filter((g) => g.status !== "Resolved").length} ${t("open", "పెండింగ్")}`}>
              {farmer.grievances.length ? farmer.grievances.map((g) => (
                <div key={g.grievance_id} className="row between griev">
                  <span><b>{g.grievance_id}</b> {tv(g.category)}<br /><small className="muted">{date(g.created_on)} · {tv(g.channel)}</small></span>
                  <span className={`pill ${statusColor(g.status)}`}>{tv(g.status)}</span>
                </div>
              )) : <p className="muted">{t("No grievances filed.", "ఫిర్యాదులు ఏవీ లేవు.")}</p>}
              <h4>{t("Raise a new grievance", "కొత్త ఫిర్యాదు చేయండి")}</h4>
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                {cats.map((c) => <option key={c} value={c}>{tv(c)}</option>)}
              </select>
              <textarea rows={3} placeholder={t("Describe the problem", "సమస్య ఏమిటో రాయండి")} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              <button className="primary" onClick={submitGrievance}>{t("Submit grievance", "ఫిర్యాదు పంపండి")}</button>
              {msg && <div className="success">{t(msg[0], msg[1])}</div>}
            </Section>

            <Section icon="🌦️" title={t("Weather")} hint={te ? farmer.district_te : farmer.district}>
              <div className="weather">
                {farmer.weather.map((w) => (
                  <div key={w.date} className="wday" title={te ? w.condition_te : w.condition}>
                    <small>{weekday(w.date)}</small>
                    <div className="wicon">{w.rain_mm ? (w.condition === "Thunderstorm" ? "⛈️" : "🌧️") : w.condition === "Sunny" ? "☀️" : "⛅"}</div>
                    <b>{w.max_c}°</b><small>{w.min_c}°</small>
                    {w.rain_mm > 0 && <small className="rain">{w.rain_mm}{t("mm", " మి.మీ.")}</small>}
                  </div>
                ))}
              </div>
            </Section>

            <Section icon="🌱" title={t("Advisory", "సలహాలు")} hint={Object.keys(farmer.advisories).map(tc).join(", ")}>
              {Object.entries(farmer.advisories).map(([crop, a]) => (
                <div key={crop}><b>{tc(crop)}</b><ul>{(te && a.te ? a.te : a.en).slice(0, 3).map((l) => <li key={l}>{l}</li>)}</ul></div>
              ))}
            </Section>
          </aside>
        </div>
      )}
    </div>
  );
}

// One row on the right: icon, name, a short hint and ›. Tap to open or close what it contains.
function Section({ icon, title, hint, children }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`side-sec ${open ? "open" : ""}`}>
      <button className="side-head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className="side-icon">{icon}</span>
        <span className="side-title">{title}{hint !== undefined && hint !== "" && <small>{hint}</small>}</span>
        <span className="side-arrow">›</span>
      </button>
      {open && <div className="side-body">{children}</div>}
    </div>
  );
}

const rupees = (n) => `₹${n.toLocaleString("en-IN")}`;
// Payment status: where the money of each scheme is right now
function Payments({ farmer }) {
  const { te, t, tv, date } = useLang();
  const paid = farmer.applications.filter((a) => a.amount);
  const step = (a) =>
    a.status === "Credited" ? ["green", "✅", t(`Credited on ${date(a.credited_on)} to ${farmer.bank}`, `${date(a.credited_on)} న ${farmer.bank} ఖాతాలో జమ అయింది`)]
    : a.status === "Approved" ? ["amber", "⏳", t("Approved — money will reach your bank soon", "ఆమోదం పొందింది — త్వరలో మీ ఖాతాలో జమ అవుతుంది")]
    : a.status.startsWith("Rejected") ? ["red", "❌", t("Not paid — application rejected. Raise a complaint under Grievances.", "చెల్లించలేదు — దరఖాస్తు తిరస్కరించబడింది. ఫిర్యాదులు లో ఫిర్యాదు చేయండి.")]
    : ["amber", "🔎", t("Not paid yet — application is being checked", "ఇంకా చెల్లించలేదు — దరఖాస్తు పరిశీలనలో ఉంది")];
  return (
    <div>
      <p className="muted">{t("Bank account", "బ్యాంకు ఖాతా")}: <b>{farmer.bank}</b></p>
      {paid.length ? paid.map((a) => {
        const [color, icon, note] = step(a);
        return (
          <div key={a.app_id} className="pay-row">
            <span className="pay-icon">{icon}</span>
            <span className="pay-main"><b>{te && a.scheme_te ? a.scheme_te : a.scheme}</b><small className="muted">{note}</small></span>
            <span className="pay-amt"><b>{rupees(a.amount)}</b><span className={`pill ${color}`}>{tv(a.status)}</span></span>
          </div>
        );
      }) : <p className="muted">{t("No scheme payments for you yet.", "మీకు ఇంకా పథకం డబ్బు ఏదీ లేదు.")}</p>}
    </div>
  );
}
