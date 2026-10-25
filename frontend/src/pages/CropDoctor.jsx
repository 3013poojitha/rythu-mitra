import { useEffect, useRef, useState } from "react";
import { api } from "../api.jsx";

const CROPS = ["Paddy", "Cotton", "Maize", "Chilli", "Red gram", "Groundnut", "Turmeric", "Soybean"];

const L = {
  en: {
    title: "Crop Doctor", sub: "Upload a photo of the affected plant. We identify the problem and tell you exactly what to spray, how much, and when.",
    crop: "Crop (optional - improves accuracy)", notSure: "Not sure", acres: "Your field size (acres)", photo: "Choose or take a photo",
    detect: "Detect disease", detecting: "Checking photo…", why: "Why it happens", symptoms: "Symptoms to confirm",
    plan: "Treatment plan", prevention: "Prevention for next time", safety: "Safety while spraying", library: "Disease library",
    libSub: "Browse common problems and spray plans without a photo.", perL: "Dose per litre", perTank: "Per {t}-L tank",
    tanks: "Tanks needed", water: "Total water", buy: "Total product needed", when: "When to apply", repeat: "Repeat", phi: "Stop before harvest",
    days: "days", method: "How", reason: "Why this", chemical: "Chemical", organic: "Organic / low-cost", conf: "confidence",
    mock: "Mock AI mode: the photo is not really analysed - a matching problem is picked from the library. Add an API key for real photo analysis.",
    disclaimer: "Doses are demo values based on common recommendations. Always read the product label and confirm with your AEO.",
    forArea: "for {a} acre(s)",
  },
  te: {
    title: "పంట వైద్యుడు", sub: "తెగులు సోకిన మొక్క ఫోటో పంపండి. సమస్యను గుర్తించి, ఏ మందు, ఎంత మోతాదు, ఎప్పుడు పిచికారీ చేయాలో చెబుతాం.",
    crop: "పంట (ఐచ్ఛికం - ఖచ్చితత్వం పెరుగుతుంది)", notSure: "తెలియదు", acres: "మీ పొలం విస్తీర్ణం (ఎకరాలు)", photo: "ఫోటో ఎంచుకోండి / తీయండి",
    detect: "తెగులు గుర్తించండి", detecting: "ఫోటో పరిశీలిస్తున్నాం…", why: "ఎందుకు వస్తుంది", symptoms: "నిర్ధారించుకోవాల్సిన లక్షణాలు",
    plan: "నివారణ ప్రణాళిక", prevention: "ముందు జాగ్రత్తలు", safety: "పిచికారీ భద్రత", library: "తెగుళ్ల సమాచారం",
    libSub: "ఫోటో లేకుండా సాధారణ సమస్యలు, మందుల ప్రణాళికలు చూడండి.", perL: "లీటరుకు మోతాదు", perTank: "{t} లీటర్ల ట్యాంకుకు",
    tanks: "ట్యాంకులు", water: "మొత్తం నీరు", buy: "కొనవలసిన మందు", when: "ఎప్పుడు", repeat: "మళ్లీ", phi: "కోతకు ముందు ఆపండి",
    days: "రోజులు", method: "ఎలా", reason: "ఎందుకు", chemical: "రసాయన మందు", organic: "సేంద్రియ / తక్కువ ఖర్చు", conf: "నమ్మకం",
    mock: "మాక్ AI మోడ్: ఫోటో నిజంగా పరిశీలించబడలేదు. నిజమైన విశ్లేషణ కోసం API కీ జోడించండి.",
    disclaimer: "మోతాదులు డెమో విలువలు. మందు లేబుల్ చదివి, మీ AEO తో నిర్ధారించుకోండి.",
    forArea: "{a} ఎకరాలకు",
  },
};

export default function CropDoctor() {
  const [lang, setLang] = useState("en");
  const [crop, setCrop] = useState("");
  const [acres, setAcres] = useState(1);
  const [provider, setProvider] = useState("claude");
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [lib, setLib] = useState(null);
  const [browse, setBrowse] = useState(null);
  const [filter, setFilter] = useState("All");
  const [error, setError] = useState("");
  const fileRef = useRef(null);
  const resultRef = useRef(null);
  const t = L[lang];

  useEffect(() => {
    api.diseases().then(setLib);
  }, []);

  function pick(f) {
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
  }

  async function detect() {
    setBusy(true);
    setError("");
    const form = new FormData();
    form.append("file", file);
    form.append("provider", provider);
    form.append("lang", lang);
    if (crop) form.append("crop", crop);
    try {
      const res = await api.diagnose(form);
      setResult(res);
      setBrowse(null);
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const byId = (id) => lib?.diseases.find((d) => d.id === id);
  const shown = browse ? byId(browse) : result?.diagnosis?.disease_id ? byId(result.diagnosis.disease_id) : null;

  return (
    <div className="stack">
      <div className="doctor-top">
        <div className="panel">
          <div className="row between">
            <h2>🩺 {t.title}</h2>
            <div className="seg small-inline">
              <button className={lang === "te" ? "on" : ""} onClick={() => setLang("te")}>తెలుగు</button>
              <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>English</button>
            </div>
          </div>
          <p className="muted">{t.sub}</p>

          <div className="form-grid">
            <div>
              <label>{t.crop}</label>
              <select value={crop} onChange={(e) => setCrop(e.target.value)}>
                <option value="">{t.notSure}</option>
                {CROPS.map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label>{t.acres}</label>
              <input type="number" min="0.1" max="100" step="0.5" value={acres} onChange={(e) => setAcres(Math.max(0.1, Number(e.target.value) || 1))} />
            </div>
            <div>
              <label>AI model</label>
              <div className="seg">
                <button className={provider === "claude" ? "on" : ""} onClick={() => setProvider("claude")}>Claude</button>
                <button className={provider === "gpt" ? "on" : ""} onClick={() => setProvider("gpt")}>ChatGPT</button>
              </div>
            </div>
          </div>

          <div className={`dropzone ${preview ? "has" : ""}`} onClick={() => fileRef.current.click()}
               onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); pick(e.dataTransfer.files[0]); }}>
            {preview ? <img src={preview} alt="crop" /> : <div><div className="big-icon">📷</div>{t.photo}<br /><small className="muted">JPG / PNG, max 8 MB</small></div>}
          </div>
          <input ref={fileRef} type="file" accept="image/*" capture="environment" hidden onChange={(e) => pick(e.target.files[0])} />
          {error && <div className="error">{error}</div>}
          <button className="primary full" disabled={!file || busy} onClick={detect}>{busy ? t.detecting : t.detect}</button>
        </div>

        <div className="panel">
          <h3>{t.library}</h3>
          <p className="muted small">{t.libSub}</p>
          <div className="chips">
            {["All", ...CROPS].map((c) => <button key={c} className={filter === c ? "on" : ""} onClick={() => setFilter(c)}>{c}</button>)}
          </div>
          <div className="lib-list">
            {lib?.diseases.filter((d) => filter === "All" || d.crop === filter).map((d) => (
              <div key={d.id} className={`lib-item ${shown?.id === d.id ? "sel" : ""}`}
                   onClick={() => { setBrowse(d.id); setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth" }), 50); }}>
                <b>{lang === "te" ? d.name_te : d.name}</b>
                <small className="muted">{lang === "te" ? d.crop_te : d.crop} · {d.type}</small>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div ref={resultRef} />
      {result && !browse && result.diagnosis.status !== "detected" && (
        <div className="panel">
          <h2>{result.diagnosis.name}</h2>
          {result.diagnosis.observed && <p>{result.diagnosis.observed}</p>}
          <p>{result.diagnosis.remedy}</p>
        </div>
      )}
      {shown && (
        <Report d={shown} t={t} lang={lang} acres={acres} tank={lib.sprayer_tank_l} safety={lib.safety[lang]}
                diag={!browse ? result?.diagnosis : null} mode={!browse ? result?.mode : null} />
      )}
    </div>
  );
}

function Report({ d, t, lang, acres, tank, safety, diag, mode }) {
  const te = lang === "te";
  const groups = [["Chemical", t.chemical], ["Organic", t.organic]];
  return (
    <div className="panel report">
      <div className="report-head">
        <div>
          <span className="tag stage">{d.type}</span>
          <h2>{te ? d.name_te : d.name}</h2>
          <p className="muted">{te ? d.crop_te : d.crop}</p>
        </div>
        {diag && (
          <div className="conf">
            <b>{Math.round(diag.confidence * 100)}%</b><small>{t.conf}</small>
            <div className="progress"><div style={{ width: `${diag.confidence * 100}%` }} /></div>
          </div>
        )}
      </div>
      {diag && mode === "mock" && <div className="banner inline">{t.mock}</div>}
      {diag?.observed && <p><b>📸</b> {diag.observed}</p>}

      <div className="grid2">
        <div className="info-box"><h4>❓ {t.why}</h4><p>{te ? d.cause_te : d.cause}</p></div>
        <div className="info-box"><h4>🔍 {t.symptoms}</h4><p>{te ? d.symptoms_te : d.symptoms}</p></div>
      </div>

      <h3 className="mt">💊 {t.plan} — {t.forArea.replace("{a}", acres)}</h3>
      {groups.map(([kind, label]) => {
        const rows = d.treatments.filter((x) => x.kind === kind);
        if (!rows.length) return null;
        return (
          <div key={kind}>
            <h4 className={kind === "Organic" ? "ok" : ""}>{label}</h4>
            <div className="treat-grid">
              {rows.map((x, i) => <Treatment key={x.product} x={x} t={t} acres={acres} tank={tank} first={kind === "Chemical" && i === 0} />)}
            </div>
          </div>
        );
      })}
      <p className="hint">⚠️ {t.disclaimer}</p>

      <div className="grid2 mt">
        <div className="info-box"><h4>🛡️ {t.prevention}</h4><ul>{(te ? d.prevention_te : d.prevention).map((p) => <li key={p}>{p}</li>)}</ul></div>
        <div className="info-box warn"><h4>🧤 {t.safety}</h4><ul>{safety.map((s) => <li key={s}>{s}</li>)}</ul></div>
      </div>
    </div>
  );
}

const fmt = (n, unit) => {
  if (unit === "g" && n >= 1000) return `${+(n / 1000).toFixed(2)} kg`;
  if (unit === "ml" && n >= 1000) return `${+(n / 1000).toFixed(2)} L`;
  return `${+n.toFixed(1)} ${unit}`;
};

function Treatment({ x, t, acres, tank, first }) {
  const perLitre = x.per === "litre";
  const water = perLitre ? x.water_l_per_acre * acres : 0;
  return (
    <div className={`treat ${first ? "best" : ""}`}>
      <div className="row between">
        <b>{x.product}</b>
        {first && <span className="pill green">Recommended</span>}
      </div>
      <p className="small muted">{t.reason}: {x.reason}</p>
      <div className="dose-grid">
        {perLitre ? (
          <>
            <div><small>{t.perL}</small><b>{x.dose} {x.unit}</b></div>
            <div><small>{t.perTank.replace("{t}", tank)}</small><b>{fmt(x.dose * tank, x.unit)}</b></div>
            <div><small>{t.tanks}</small><b>{Math.ceil(water / tank)}</b></div>
            <div><small>{t.water}</small><b>{Math.round(water)} L</b></div>
            <div className="hl"><small>{t.buy}</small><b>{fmt(x.dose * water, x.unit)}</b></div>
          </>
        ) : (
          <>
            <div><small>Per acre</small><b>{x.dose} {x.unit}</b></div>
            <div className="hl"><small>{t.buy}</small><b>{fmt(x.dose * acres, x.unit)}</b></div>
          </>
        )}
      </div>
      <div className="small"><b>{t.method}:</b> {x.method}</div>
      <div className="small"><b>{t.when}:</b> {x.when}</div>
      <div className="small"><b>{t.repeat}:</b> {x.repeat}</div>
      {x.phi_days && <div className="small"><b>{t.phi}:</b> {x.phi_days} {t.days}</div>}
    </div>
  );
}
