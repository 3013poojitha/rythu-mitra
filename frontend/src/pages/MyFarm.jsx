import { useEffect, useRef, useState } from "react";
import { api } from "../api.jsx";
import { useLang } from "../i18n.jsx";

let CROP_ICON = {};
export const cropIcon = (c) => CROP_ICON[c] || "🌱";

// Choices for crop/soil/season pickers; also fills the crop icon table
export function useProfileOptions() {
  const [opts, setOpts] = useState(null);
  useEffect(() => {
    api.profileOptions().then((o) => {
      CROP_ICON = Object.fromEntries(o.crops.map((c) => [c.name, c.icon]));
      setOpts(o);
    }).catch(() => {});
  }, []);
  return opts;
}

const WATER_ICON = { Borewell: "🚰", Canal: "🌊", Tank: "💧", Rainfed: "🌧️", Drip: "💧", Sprinkler: "💦" };
const PERSONAL = ["name", "village", "district", "age", "gender"];
const GROUP_TE = {
  Cereals: "ధాన్యాలు", Commercial: "వాణిజ్య పంటలు", Pulses: "పప్పు ధాన్యాలు", Spices: "సుగంధ ద్రవ్యాలు", Oilseeds: "నూనె గింజలు",
  Vegetables: "కూరగాయలు", Fruits: "పండ్లు", Flowers: "పూలు", Fodder: "పశుగ్రాసం",
};
const masked = (m) => `${m.slice(0, 2)}xxxxxx${m.slice(-2)}`;

// Farmer's profile, land and crops, with an edit form that saves to their account.
// view: "full" (details + Edit), "home" (just the Namaskaram card), "setup" (a new farmer fills everything first)
export default function MyFarm({ farmer, isFarmer, onSaved, view = "full", onBack }) {
  const { te, t, tv, tc, td, terr, date, time } = useLang();
  const [editing, setEditing] = useState(false);
  const opts = useProfileOptions();
  const [form, setForm] = useState(null);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  const setup = view === "setup";
  useEffect(() => {
    setEditing(false);
    setSaved(false);
  }, [farmer.farmer_id]);
  // A new farmer starts on an empty form (only the name and district from the AEO record are filled in)
  useEffect(() => {
    if (setup && opts && !editing) {
      setForm({ name: farmer.name, district: farmer.district, village: "", age: "", gender: "", plots: [blankPlot()] });
      setEditing(true);
    }
  }, [setup, opts]);

  function startEdit() {
    const f = {};
    PERSONAL.forEach((k) => (f[k] = farmer[k]));
    f.plots = farmer.plots.map((p) => ({ ...p }));
    setForm(f);
    setError("");
    setSaved(false);
    setEditing(true);
  }

  const set = (k, v) => setForm({ ...form, [k]: v });
  const setPlot = (i, k, v) => set("plots", form.plots.map((p, j) => (j === i ? { ...p, [k]: v } : p)));
  const blankPlot = () => ({ survey_no: "", area_acres: "", crop: "", soil: "", irrigation: "", season: "Kharif" });
  const addPlot = () => set("plots", [...form.plots, blankPlot()]);
  const removePlot = (i) => set("plots", form.plots.filter((_, j) => j !== i));
  // Options show Telugu but keep the English value the backend expects
  // An empty value shows "Choose…" until the farmer picks one
  const options = (list, value) => [
    !value && <option key="" value="" disabled>{t("Choose…", "ఎంచుకోండి…")}</option>,
    ...list.map((v) => <option key={v} value={v}>{tv(v)}</option>),
  ];

  async function save() {
    setError("");
    setBusy(true);
    try {
      const updated = await api.updateFarmer(farmer.farmer_id, {
        ...form,
        age: Number(form.age),
        plots: form.plots.map((p) => ({ ...p, area_acres: Number(p.area_acres) })),
      });
      onSaved(updated);
      setEditing(false);
      setSaved(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (editing && form && opts) {
    const total = form.plots.reduce((s, p) => s + (Number(p.area_acres) || 0), 0);
    return (
      <div className="panel farm-edit">
        {setup ? (
          <div className="setup-head">
            <h2>🙏 {t("Welcome to Rythu Mitra!", "రైతు మిత్రకు స్వాగతం!")}</h2>
            <p className="muted">{t("Before you start, please fill in your details, your land and your crops. We use them to give you the right advice.",
              "మొదలుపెట్టే ముందు మీ వివరాలు, మీ భూమి, మీ పంటలు నింపండి. వీటితోనే మీకు సరైన సలహా ఇస్తాము.")}</p>
            <span className="muted small">{t("Farmer ID", "రైతు ID")} {farmer.farmer_id}</span>
          </div>
        ) : (
          <div className="row between wrap">
            <h2>✏️ {isFarmer ? t("Edit my details", "నా వివరాలు మార్చండి") : t("Edit farmer details", "రైతు వివరాలు మార్చండి")}</h2>
            <span className="muted small">{farmer.farmer_id}</span>
          </div>
        )}

        <h3 className="mt">👤 {t("Personal details", "వ్యక్తిగత వివరాలు")}</h3>
        <div className="form-grid">
          <div><label>{t("Full name")}</label><input value={form.name} onChange={(e) => set("name", e.target.value)} /></div>
          <div><label>{t("Village")}</label><input value={form.village} onChange={(e) => set("village", e.target.value)} /></div>
          <div>
            <label>{t("District")}</label>
            <select value={form.district} onChange={(e) => set("district", e.target.value)}>
              {opts.districts.map((d) => <option key={d} value={d}>{td(d)}</option>)}
            </select>
          </div>
          <div><label>{t("Age")}</label><input type="number" min="18" max="100" value={form.age} onChange={(e) => set("age", e.target.value)} /></div>
          <div>
            <label>{t("Gender")}</label>
            <select value={form.gender} onChange={(e) => set("gender", e.target.value)}>{options(opts.genders, form.gender)}</select>
          </div>
          <div>
            <label>{t("Mobile & bank", "మొబైల్ & బ్యాంక్")}</label>
            <input value={`${masked(farmer.mobile)} · ${farmer.bank}`} disabled />
            <small className="muted">{t("To change these, visit your AEO with proof.", "వీటిని మార్చడానికి రుజువు పత్రాలతో మీ AEO ని కలవండి.")}</small>
          </div>
        </div>

        <div className="row between wrap">
          <h3>🗺️ {t("Land & crops", "భూమి & పంటలు")}</h3>
          <span className="pill green">{t("Total", "మొత్తం")} {Math.round(total * 100) / 100} {t("acres")}</span>
        </div>
        {form.plots.map((p, i) => (
          <div key={i} className="plot-edit">
            <div className="row between">
              <b>{t("Plot")} {i + 1}</b>
              {form.plots.length > 1 && <button className="link danger" onClick={() => removePlot(i)}>🗑 {t("Remove", "తీసివేయండి")}</button>}
            </div>
            <div className="plot-grid">
              <div><label>{t("Survey no.")}</label><input value={p.survey_no} placeholder={t("e.g. 123/A", "ఉదా. 123/A")} onChange={(e) => setPlot(i, "survey_no", e.target.value)} /></div>
              <div><label>{t("Area (acres)")}</label><input type="number" step="0.1" min="0.1" value={p.area_acres} onChange={(e) => setPlot(i, "area_acres", e.target.value)} /></div>
              <div>
                <label>{t("Crop")}</label>
                <CropPicker value={p.crop} crops={opts.crops} onChange={(v) => setPlot(i, "crop", v)} />
              </div>
              <div>
                <label>{t("Season")}</label>
                <select value={p.season} onChange={(e) => setPlot(i, "season", e.target.value)}>{options(opts.seasons, p.season)}</select>
              </div>
              <div>
                <label>{t("Soil")}</label>
                <select value={p.soil} onChange={(e) => setPlot(i, "soil", e.target.value)}>{options(opts.soils, p.soil)}</select>
              </div>
              <div>
                <label>{t("Water source")}</label>
                <select value={p.irrigation} onChange={(e) => setPlot(i, "irrigation", e.target.value)}>{options(opts.irrigation, p.irrigation)}</select>
              </div>
              {/* When this crop was sown and when the harvest is expected (both optional) */}
              <div>
                <label>🌱 {t("Sown on", "విత్తిన తేదీ")}</label>
                <input type="date" value={p.sown_on || ""} onChange={(e) => setPlot(i, "sown_on", e.target.value)} />
              </div>
              <div>
                <label>🧺 {t("Harvest by", "కోత అంచనా తేదీ")}</label>
                <input type="date" value={p.harvest_by || ""} min={p.sown_on || undefined} onChange={(e) => setPlot(i, "harvest_by", e.target.value)} />
              </div>
            </div>
          </div>
        ))}
        {form.plots.length < opts.max_plots && <button className="add-plot" onClick={addPlot}>＋ {t("Add another plot", "ఇంకో భూమి ముక్క జోడించండి")}</button>}

        {error && <div className="error">{terr(error)}</div>}
        <div className="row end">
          {!setup && <button onClick={() => setEditing(false)} disabled={busy}>{t("Cancel")}</button>}
          <button className="primary" onClick={save} disabled={busy}>
            {busy ? t("Saving…", "సేవ్ అవుతోంది…") : setup ? `✅ ${t("Save and start", "సేవ్ చేసి మొదలుపెట్టండి")}` : `💾 ${t("Save changes")}`}
          </button>
        </div>
      </div>
    );
  }

  if (setup) return <div className="panel center pad">{t("Loading…", "లోడ్ అవుతోంది…")}</div>;

  const first = farmer.name.split(" ")[0];
  const hero = (
      <div className="panel farm-hero">
        <div className="row between wrap">
          <div className="row">
            <div className="farm-avatar">{farmer.name[0]}</div>
            <div>
              <h2>{isFarmer ? t(`Namaskaram, ${first} 🙏`, `నమస్కారం, ${first} గారు 🙏`) : farmer.name}</h2>
              <p className="muted">
                {farmer.farmer_id} · 📍 {farmer.village}, {te ? <span className="te">{farmer.district_te}</span> : farmer.district}
                {" "}· {t("Age")} {farmer.age} · {tv(farmer.gender)}
              </p>
            </div>
          </div>
          <div className="row gap-sm">
            {view === "full" && <button className="primary" onClick={startEdit} disabled={!opts}>✏️ {isFarmer ? t("Edit my details", "నా వివరాలు మార్చండి") : t("Edit details")}</button>}
            {onBack && <button onClick={onBack}>← {t("Back", "వెనక్కి")}</button>}
          </div>
        </div>
        {saved && <div className="success">{t("Saved to your account")} ✓</div>}
      </div>
  );
  // Home page: just the greeting; the details and Edit live under 👤 My details in the top-right menu
  if (view === "home") return hero;

  return (
    <div className="stack">
      {hero}

      <div className="farm-stats">
        <div className="kpi"><small>{t("Total land")}</small><b>{farmer.total_acres} <span className="unit">{t("acres")}</span></b></div>
        <div className="kpi"><small>{t("Land plots")}</small><b>{farmer.plots.length}</b></div>
        <div className="kpi"><small>{t("Crops")}</small><b>{farmer.crops.length}</b><span className="crop-chips">{farmer.crops.map((c) => <span key={c}>{cropIcon(c)} {tc(c)}</span>)}</span></div>
        <div className="kpi"><small>{t("Bank & mobile", "బ్యాంక్ & మొబైల్")}</small><b className="kpi-text">{farmer.bank}</b><small>{t("Mobile")} {masked(farmer.mobile)}</small></div>
      </div>

      <div className="panel">
        <div className="row between wrap">
          <h3>🗺️ {isFarmer ? t("My land & crops", "నా భూమి & పంటలు") : t("Land & crops", "భూమి & పంటలు")} <span className="tag stage">{t("Stage 4", "దశ 4")}</span></h3>
          {farmer.updated_on && <span className="muted small">{t("Last updated", "చివరిగా మార్చింది")} {date(farmer.updated_on)}, {time(farmer.updated_on)}</span>}
        </div>
        <div className="plot-cards">
          {farmer.plots.map((p) => (
            <div key={p.survey_no} className="plot-card">
              <div className="plot-crop">{cropIcon(p.crop)}</div>
              <div className="grow">
                <div className="row between"><b>{tc(p.crop)}</b><span className="pill green">{p.area_acres} {t("ac", "ఎకరాలు")}</span></div>
                <small className="muted">{t("Survey", "సర్వే నం.")} {p.survey_no} · {tv(p.season)}</small>
                <div className="plot-meta"><span>🟫 {tv(p.soil)}</span><span>{WATER_ICON[p.irrigation] || "💧"} {tv(p.irrigation)}</span></div>
                <CropDates p={p} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// "Sown 10 Jun 2026 → harvest by 30 Nov 2026 · 33 days left" under a crop card
function CropDates({ p }) {
  const { te, t, date } = useLang();
  if (!p.sown_on && !p.harvest_by) {
    return <small className="muted crop-dates">📅 {t("Add sowing and harvest dates in Edit", "విత్తిన / కోత తేదీలు మార్చండి లో జోడించండి")}</small>;
  }
  // Both dates at local midnight, so the count does not shift by the time zone
  const days = p.harvest_by ? Math.round((new Date(`${p.harvest_by}T00:00`) - new Date(new Date().toDateString())) / 86400000) : null;
  return (
    <div className="crop-dates">
      {p.sown_on && <span>🌱 {t("Sown", "విత్తింది")} <b>{date(p.sown_on)}</b></span>}
      {p.harvest_by && <span>🧺 {t("Harvest by", "కోత")} <b>{date(p.harvest_by)}</b></span>}
      {days != null && days >= 0 && <span className="pill green">{te ? `${days} రోజులు మిగిలాయి` : `${days} days left`}</span>}
      {days != null && days < 0 && <span className="pill amber">{t("Harvest date passed", "కోత తేదీ దాటింది")}</span>}
    </div>
  );
}

// Type-to-search crop box: matches English or Telugu names; any other name can be typed too
export function CropPicker({ value, crops, onChange }) {
  const { te, t } = useLang();
  const [open, setOpen] = useState(false);
  const [hi, setHi] = useState(0);
  const box = useRef(null);
  const q = value.trim().toLowerCase();
  const matches = (q ? crops.filter((c) => c.name.toLowerCase().includes(q) || c.te.includes(value.trim())) : crops)
    .sort((a, b) => (q ? a.name.toLowerCase().startsWith(q) ? -1 : b.name.toLowerCase().startsWith(q) ? 1 : 0 : 0))
    .slice(0, 8);
  const exact = crops.find((c) => c.name.toLowerCase() === q);
  // A picked crop is stored by its English name; in Telugu mode the box shows the Telugu name
  const shown = te && exact ? exact.te : value;

  useEffect(() => {
    const close = (e) => box.current && !box.current.contains(e.target) && setOpen(false);
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  function pick(name) {
    onChange(name);
    setOpen(false);
  }

  function onKey(e) {
    if (e.key === "ArrowDown") { e.preventDefault(); setOpen(true); setHi((h) => Math.min(h + 1, matches.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setHi((h) => Math.max(h - 1, 0)); }
    else if (e.key === "Enter" && open && matches[hi]) { e.preventDefault(); pick(matches[hi].name); }
    else if (e.key === "Escape") setOpen(false);
  }

  return (
    <div className="crop-picker" ref={box}>
      <span className="crop-picker-icon">{value ? cropIcon(value) : "🔍"}</span>
      <input
        value={shown}
        placeholder={t("Type a crop, e.g. jowar", "పంట పేరు రాయండి, ఉదా. జొన్న")}
        onFocus={() => setOpen(true)}
        onChange={(e) => { onChange(e.target.value); setOpen(true); setHi(0); }}
        onKeyDown={onKey}
      />
      {open && (
        <div className="crop-menu">
          {matches.map((c, i) => (
            <div key={c.name} className={`crop-opt ${i === hi ? "hi" : ""}`} onMouseDown={(e) => { e.preventDefault(); pick(c.name); }} onMouseEnter={() => setHi(i)}>
              <span>{c.icon}</span><b>{te ? c.te : c.name}</b><span className="te">{te ? c.name : c.te}</span><small>{te ? GROUP_TE[c.group] || c.group : c.group}</small>
            </div>
          ))}
          {q && !exact && !matches.length && <div className="crop-opt new">➕ {t(`Use "${value.trim()}" as a new crop`, `"${value.trim()}" ను కొత్త పంటగా వాడండి`)}</div>}
          {q && !exact && matches.length > 0 && <div className="crop-hint">{t("Not in the list? Keep typing — any crop name is allowed.", "జాబితాలో లేదా? రాస్తూ ఉండండి — ఏ పంట పేరైనా రాయవచ్చు.")}</div>}
        </div>
      )}
    </div>
  );
}
