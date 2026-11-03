import ReadAloud from "../ReadAloud.jsx";
import { useEffect, useState } from "react";
import { api } from "../api.jsx";
import { useLang } from "../i18n.jsx";
import MyFarm from "./MyFarm.jsx";
import Chat from "./Chat.jsx";
import { DiseaseLibrary } from "./CropDoctor.jsx";

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
  const [openSec, setOpenSec] = useState(null); // right panel: only one section open at a time

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
            {/* Farmers see just their greeting here; editing is under 👤 My details (top right) */}
            <MyFarm farmer={farmer} isFarmer={isFarmer} view={isFarmer ? "home" : "full"}
                    onSaved={(f) => { setFarmer(f); api.farmers().then(setFarmers); refreshUser?.(); }} />
            {/* Farmers ask questions right here: type, or tap the mic and talk */}
            {isFarmer && <div className="panel"><Chat user={user} waOpen={waOpen} embedded /></div>}
          </div>

          {/* Right side: tap a row to open what it contains */}
          <aside className="svc-side">
            <Section id="advice" openId={openSec} setOpenId={setOpenSec} icon="🌱" title={t("Advisory", "సలహాలు")}>
              {Object.entries(farmer.advisories).map(([crop, a]) => (
                <div key={crop}><b>{tc(crop)}</b><ul>{(te && a.te ? a.te : a.en).slice(0, 3).map((l) => <li key={l}>{l}</li>)}</ul></div>
              ))}
              {farmer.next_crops?.length > 0 && <NextCrops plans={farmer.next_crops} />}
            </Section>

            <Section id="apps" openId={openSec} setOpenId={setOpenSec} icon="📋" title={t("Scheme applications")}>
              {farmer.applications.map((a) => (
                <div key={a.app_id} className="side-row">
                  <span className="grow"><b>{te && a.scheme_te ? a.scheme_te : a.scheme}</b><small className="muted">{a.app_id}</small></span>
                  <span className="pay-amt">
                    <span className={`pill ${statusColor(a.status)}`}>{tv(a.status)}</span>
                    <small>{a.amount ? rupees(a.amount) : "—"}</small>
                  </span>
                </div>
              ))}
              <ApplyScheme farmer={farmer} onApplied={() => api.farmer(id).then(setFarmer)} />
            </Section>

            <Section id="pay" openId={openSec} setOpenId={setOpenSec} icon="💰" title={t("Payment status", "డబ్బు జమ స్థితి")}>
              <Payments farmer={farmer} />
            </Section>

            <Section id="griev" openId={openSec} setOpenId={setOpenSec} icon="📣" title={t("Grievances")}>
              {farmer.grievances.length ? farmer.grievances.map((g) => (
                <div key={g.grievance_id} className="row between griev">
                  <span><b>{g.grievance_id}</b> {tv(g.category)}<br /><small className="muted">{date(g.created_on)} · {tv(g.channel)}</small></span>
                  <span className={`pill ${statusColor(g.status)}`}>{tv(g.status)}</span>
                </div>
              )) : <p className="muted">{t("No grievances filed.", "ఫిర్యాదులు ఏవీ లేవు.")}</p>}
              <h4 className="no-read">{t("Raise a new grievance", "కొత్త ఫిర్యాదు చేయండి")}</h4>
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                {cats.map((c) => <option key={c} value={c}>{tv(c)}</option>)}
              </select>
              <textarea rows={3} placeholder={t("Describe the problem", "సమస్య ఏమిటో రాయండి")} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              <button className="primary" onClick={submitGrievance}>{t("Submit grievance", "ఫిర్యాదు పంపండి")}</button>
              {msg && <div className="success">{t(msg[0], msg[1])}</div>}
            </Section>

            <Section id="weather" openId={openSec} setOpenId={setOpenSec} icon="🌦️" title={t("Weather")} hint={te ? farmer.district_te : farmer.district}>
              <div className="weather">
                {farmer.weather.map((w) => (
                  <div key={w.date} className="wday" title={te ? w.condition_te : w.condition}
                       data-say={te ? `${weekday(w.date)}: ${w.condition_te}, గరిష్ఠం ${w.max_c} డిగ్రీలు, కనిష్ఠం ${w.min_c}${w.rain_mm ? `, వర్షం ${w.rain_mm} మిల్లీమీటర్లు` : ""}`
                         : `${weekday(w.date)}: ${w.condition}, high ${w.max_c} degrees, low ${w.min_c}${w.rain_mm ? `, rain ${w.rain_mm} millimetres` : ""}`}>
                    <small>{weekday(w.date)}</small>
                    <div className="wicon">{w.rain_mm ? (w.condition === "Thunderstorm" ? "⛈️" : "🌧️") : w.condition === "Sunny" ? "☀️" : "⛅"}</div>
                    <b>{w.max_c}°</b><small>{w.min_c}°</small>
                    {w.rain_mm > 0 && <small className="rain">{w.rain_mm}{t("mm", " మి.మీ.")}</small>}
                  </div>
                ))}
              </div>
            </Section>

            <Section id="library" openId={openSec} setOpenId={setOpenSec} icon="📚" title={t("Disease library", "తెగుళ్ల సమాచారం")}>
              <DiseaseLibrary key={farmer.farmer_id} farmer={farmer} />
            </Section>
          </aside>
        </div>
      )}
    </div>
  );
}

// One row on the right: icon, name, a short hint and ›. Tap to open or close what it contains.
// Only one is open at a time: opening one closes the other (openId is shared by the panel)
function Section({ id, openId, setOpenId, icon, title, hint, children }) {
  const open = openId === id;
  const setOpen = (o) => setOpenId(o ? id : null);
  return (
    <div className={`side-sec ${open ? "open" : ""}`}>
      <button className="side-head" onClick={() => setOpen(!open)} aria-expanded={open}>
        {/* icons hidden for now (the icon prop is kept, to bring them back later) */}
        <span className="side-title">{title}{hint !== undefined && hint !== "" && <small>{hint}</small>}</span>
        <span className="side-arrow">›</span>
      </button>
      {open && <div className="side-body" data-read><ReadAloud />{children}</div>}
    </div>
  );
}

// Advisory: what each plot could grow next - the best crop in full (why, when to sow, seed,
// fertilizer, harvest, money), then the other choices in one line (backend/app/next_crop.py)
function NextCrops({ plans }) {
  const { lang, t } = useLang();
  return (
    <>
      <div className="nc-title">🔄 {t("What to grow next", "తర్వాత ఏ పంట వేయవచ్చు")}</div>
      {plans.map((pl) => {
        const best = pl.picks[0];
        const w = best[lang];
        return (
          <div key={pl.survey_no} className="nc-card">
            <div className="nc-plot">{pl[lang].head}</div>
            <div className="nc-best">{best.icon} <b>{w.name}</b><span className="pill soft">{w.season}</span>
              <span className="nc-tag">{t("Best choice", "మంచి ఎంపిక")}</span></div>
            <ul className="nc-why">{w.why.map((x) => <li key={x}>{x}</li>)}</ul>
            <div className="nc-grid">
              <div>📅 {w.sow}</div><div>🌱 {w.seed}</div><div>🧪 {w.fert}</div><div>⏳ {w.harvest}</div><div>🧺 {w.yield}</div>
            </div>
            <div className="nc-money">💰 {w.money}</div>
            {pl.picks.length > 1 && <div className="nc-others"><b>{t("Other choices", "ఇతర ఎంపికలు")}:</b> {pl.picks.slice(1).map((x) => x[lang].short).join(", ")}</div>}
          </div>
        );
      })}
      <p className="muted small">{t("Demo estimates from soil, water, season, crop rotation and market price. Check with your AEO and a soil test before sowing.",
        "నేల, నీరు, కాలం, పంట మార్పిడి, మార్కెట్ ధర ఆధారంగా డెమో అంచనాలు. విత్తే ముందు మీ AEO ని అడగండి, నేల పరీక్ష చేయించండి.")}</p>
    </>
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

// ➕ Apply for a scheme: pick one, see the benefit, who can apply and what to bring, then send.
// It starts as "Pending verification" and shows in the list above.
function ApplyScheme({ farmer, onApplied }) {
  const { te, t, tv, terr } = useLang();
  const [pick, setPick] = useState("");
  const [sure, setSure] = useState(false);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(null);
  const [error, setError] = useState("");
  const open = farmer.schemes_open || [];
  const s = open.find((x) => x.id === pick);

  async function send() {
    setBusy(true);
    setError("");
    try {
      const a = await api.applyScheme({ farmer_id: farmer.farmer_id, scheme_id: pick });
      setDone(a);
      setPick("");
      setSure(false);
      onApplied();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="apply-box">
      <h4>➕ {t("Apply for a scheme", "పథకానికి దరఖాస్తు చేయండి")}</h4>
      {done && (
        <div className="success">
          ✅ {te ? `${done.scheme_te} కు దరఖాస్తు పంపాం. ID ${done.app_id}. స్థితి: ${tv(done.status)} — మీ AEO పరిశీలిస్తారు.`
            : `Application for ${done.scheme} sent. ID ${done.app_id}. Status: ${done.status} — your AEO will check it.`}
        </div>
      )}
      {!open.length ? (
        <p className="muted">{t("You have applied for every scheme.", "అన్ని పథకాలకు మీరు దరఖాస్తు చేశారు.")}</p>
      ) : (
        <>
          <select value={pick} onChange={(e) => { setPick(e.target.value); setDone(null); setError(""); }}>
            <option value="" disabled>{t("Choose a scheme…", "పథకం ఎంచుకోండి…")}</option>
            {open.map((x) => <option key={x.id} value={x.id}>{te ? x.name_te : x.name}</option>)}
          </select>
          {s && (
            <div className="apply-info">
              <p><b>💰 {t("Benefit", "లాభం")}:</b> {te ? s.benefit_te : s.benefit}</p>
              <p><b>✅ {t("Who can apply", "ఎవరు అర్హులు")}:</b> {te ? s.eligibility_te : s.eligibility}</p>
              <p><b>📄 {t("What to keep ready", "సిద్ధంగా ఉంచుకోవాల్సినవి")}:</b> {te ? s.apply_te : s.apply}</p>
              <label className="check">
                <input type="checkbox" checked={sure} onChange={(e) => setSure(e.target.checked)} />
                {t("My land and bank details in My details are correct", "నా వివరాలు లో నా భూమి, బ్యాంక్ వివరాలు సరైనవి")}
              </label>
              <button className="primary" disabled={!sure || busy} onClick={send}>
                {busy ? t("Sending…", "పంపుతున్నాం…") : `📨 ${t("Send application", "దరఖాస్తు పంపండి")}`}
              </button>
            </div>
          )}
          {error && <div className="error">{terr(error)}</div>}
        </>
      )}
    </div>
  );
}
