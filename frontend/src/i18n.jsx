import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api } from "./api.jsx";

// App language: Telugu first (most farmers read Telugu, not English), with a తెలుగు | English switch.
// Telugu words for data values, screen words and backend errors come from GET /api/terms
// (backend/app/terms.py), shared with the Streamlit app.
const LANG_KEY = "rythu_lang";

// Month names are written out here; the browser's te-IN locale is not reliable
const MONTHS_TE = ["జనవరి", "ఫిబ్రవరి", "మార్చి", "ఏప్రిల్", "మే", "జూన్", "జులై", "ఆగస్టు", "సెప్టెంబర్", "అక్టోబర్", "నవంబర్", "డిసెంబర్"];
const MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONTHS_EN_LONG = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const DAYS_TE = ["ఆది", "సోమ", "మంగళ", "బుధ", "గురు", "శుక్ర", "శని"];
const DAYS_EN = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
export const MONTH_INITIALS = { en: "JFMAMJJASOND".split(""), te: ["జ", "ఫి", "మా", "ఏ", "మే", "జూ", "జు", "ఆ", "సె", "అ", "న", "డి"] };

function savedLang() {
  try {
    return localStorage.getItem(LANG_KEY) === "en" ? "en" : "te";
  } catch {
    return "te";
  }
}

// "2026-10" or "2026-10-27" or a full ISO time -> Date in local time
function toDate(v) {
  const s = String(v || "");
  if (/^\d{4}-\d{2}$/.test(s)) return new Date(`${s}-01T00:00`);
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return new Date(`${s}T00:00`);
  return new Date(s);
}

const LangContext = createContext(null);

export function LangProvider({ children }) {
  const [lang, setLangState] = useState(savedLang);
  const [terms, setTerms] = useState({ values: {}, ui: {}, errors: [], medicines: {} });
  const [crops, setCrops] = useState({}); // English crop name -> Telugu
  const [districts, setDistricts] = useState({}); // English district name -> Telugu

  useEffect(() => {
    api.terms().then((d) => setTerms({ values: d.values || {}, ui: d.ui || {}, errors: d.errors || [], medicines: d.medicines || {} })).catch(() => {});
  }, []);
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback((l) => {
    setLangState(l);
    try {
      localStorage.setItem(LANG_KEY, l);
    } catch {
      /* storage blocked - the choice lasts until reload */
    }
  }, []);

  // Telugu crop and district names need a login, so App calls this after login
  const loadCrops = useCallback(() => {
    api.profileOptions().then((o) => setCrops(Object.fromEntries(o.crops.map((c) => [c.name, c.te])))).catch(() => {});
    api.reference().then((r) => setDistricts(r.districts || {})).catch(() => {});
  }, []);

  const value = useMemo(() => {
    const te = lang === "te";
    const errors = terms.errors.map(([p, tpl]) => [new RegExp("^" + p + "$"), tpl]);
    // t("English", "తెలుగు"); with one argument, a common screen word from the shared UI list
    const t = (en, teText) => (te ? teText ?? terms.ui[en] ?? en : en);
    const tv = (v) => (te && v != null ? terms.values[v] ?? terms.ui[v] ?? v : v);
    // Medicine name: Telugu with the English bottle label in brackets
    const tm = (name) => (te && name ? terms.medicines[name] ?? name : name);
    const terr = (msg) => {
      if (!te || !msg) return msg;
      const m = String(msg).trim();
      for (const [re, tpl] of errors) {
        const hit = m.match(re);
        if (hit) return tpl.replace(/\{(\d+)\}/g, (_, n) => hit[Number(n)] ?? "");
      }
      return msg;
    };
    const tc = (crop) => (te && crop ? crops[crop] || crops[crop.split(" (")[0]] || crop : crop);
    const td = (district) => (te && district ? districts[district] || district : district);
    // Dates: "Oct 2026", "October 2026", "27 Oct", "27 Oct 2026", "3:45 pm", "Mon 27"
    const month = (v, long = false) => {
      const d = toDate(v);
      return `${(te ? MONTHS_TE : long ? MONTHS_EN_LONG : MONTHS_EN)[d.getMonth()]} ${d.getFullYear()}`;
    };
    const day = (v) => {
      const d = toDate(v);
      return `${d.getDate()} ${(te ? MONTHS_TE : MONTHS_EN)[d.getMonth()]}`;
    };
    const date = (v) => `${day(v)} ${toDate(v).getFullYear()}`;
    const time = (v) => {
      const d = toDate(v);
      const h = d.getHours(), mm = String(d.getMinutes()).padStart(2, "0"), h12 = h % 12 || 12;
      if (!te) return `${h12}:${mm} ${h < 12 ? "am" : "pm"}`;
      const part = h < 5 ? "రాత్రి" : h < 12 ? "ఉదయం" : h < 16 ? "మధ్యాహ్నం" : h < 19 ? "సాయంత్రం" : "రాత్రి";
      return `${part} ${h12}:${mm}`;
    };
    const weekday = (v) => {
      const d = toDate(v);
      return `${(te ? DAYS_TE : DAYS_EN)[d.getDay()]} ${d.getDate()}`;
    };
    return { lang, te, setLang, t, tv, tm, terr, tc, td, month, day, date, time, weekday, loadCrops };
  }, [lang, terms, crops, districts, setLang, loadCrops]);

  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
}

export const useLang = () => useContext(LangContext);

// The తెలుగు | English pill, shown in the top bar and on the login card
export function LangSwitch({ className = "" }) {
  const { lang, setLang } = useLang();
  return (
    <div className={`seg lang-switch ${className}`} role="group" aria-label="Language / భాష">
      <button type="button" className={lang === "te" ? "on" : ""} onClick={() => setLang("te")} aria-pressed={lang === "te"}>తెలుగు</button>
      <button type="button" className={lang === "en" ? "on" : ""} onClick={() => setLang("en")} aria-pressed={lang === "en"}>English</button>
    </div>
  );
}
