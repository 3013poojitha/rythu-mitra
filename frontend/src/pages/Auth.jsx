import { useEffect, useState } from "react";
import { api, session } from "../api.jsx";
import { LangSwitch, useLang } from "../i18n.jsx";

// Login, farmer sign-up, forgot password and reset password - one card that switches between modes
export default function Auth({ onLogin, startNotice = null }) {
  const { te, t, setLang } = useLang();
  useEffect(() => setLang("te"), []); // the login page always opens in Telugu; the switch changes it
  const [mode, setMode] = useState("login");
  const [notice, setNotice] = useState(startNotice); // [English, Telugu]
  const [resetFor, setResetFor] = useState(null); // {user_id, sent_to, demo_otp}

  const go = (m, msg = null) => {
    setMode(m);
    setNotice(msg);
  };

  return (
    <div className="auth-page">
      <div className="auth-hero">
        <div className="logo big">🌾</div>
        <h1>{te ? "రైతు మిత్ర" : "Rythu Mitra"}</h1>
        <p>{t("Telangana Agriculture Department × Bharat Vistaar", "తెలంగాణ వ్యవసాయ శాఖ × భారత్ విస్తార్")}</p>
        <ul>
          <li>{t("Telugu & English farmer assistant", "తెలుగు & ఇంగ్లీష్‌లో రైతు సహాయకుడు")}</li>
          <li>{t("Crop disease detection with spray guidance", "పంట తెగులు గుర్తింపు, మందుల సలహా")}</li>
          <li>{t("Scheme, payment and grievance status", "పథకాలు, డబ్బు జమ, ఫిర్యాదుల స్థితి")}</li>
          <li>{t("Content pipeline and PMU dashboard for staff", "సిబ్బందికి కంటెంట్ పైప్‌లైన్, PMU డాష్‌బోర్డ్")}</li>
        </ul>
        <small>{t("Prototype with dummy data")}</small>
      </div>

      <div className="auth-card panel">
        <div className="auth-lang"><LangSwitch /></div>
        {notice && <div className="success">{t(notice[0], notice[1])}</div>}
        {mode === "login" && <Login onLogin={onLogin} go={go} />}
        {mode === "register" && <Register go={go} />}
        {mode === "forgot" && <Forgot go={go} onSent={(r) => { setResetFor(r); go("reset"); }} />}
        {mode === "reset" && <Reset info={resetFor} go={go} />}
      </div>
    </div>
  );
}

function Login({ onLogin, go }) {
  const { t, terr } = useLang();
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const res = await api.login({ user_id: userId, password });
      session.set(res.token, remember);
      onLogin(res.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit}>
      <h2>{t("Log in")}</h2>
      <p className="muted">{t("Farmers use their Farmer ID (e.g. TS1002) or mobile number. Staff use their department user ID.",
        "రైతులు తమ రైతు ID (ఉదా. TS1002) లేదా మొబైల్ నంబర్ వాడండి. సిబ్బంది తమ శాఖ యూజర్ ID వాడండి.")}</p>
      <label>{t("User ID or mobile number", "యూజర్ ID లేదా మొబైల్ నంబర్")}</label>
      <input value={userId} onChange={(e) => setUserId(e.target.value)} autoComplete="username" autoFocus required />
      <label>{t("Password")}</label>
      <PasswordInput value={password} onChange={setPassword} show={show} setShow={setShow} autoComplete="current-password" />
      <div className="row between auth-row">
        <label className="check"><input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} /> {t("Remember me")}</label>
        <a onClick={() => go("forgot")}>{t("Forgot password?")}</a>
      </div>
      {error && <div className="error">{terr(error)}</div>}
      <button className="primary full" disabled={busy}>{busy ? t("Logging in…", "లాగిన్ అవుతోంది…") : t("Log in")}</button>
      <p className="center muted">{t("New farmer?", "కొత్త రైతా?")} <a onClick={() => go("register")}>{t("Create an account", "ఖాతా తెరవండి")}</a></p>
    </form>
  );
}

function Register({ go }) {
  const { t, terr } = useLang();
  const [hasId, setHasId] = useState(true); // with a department Farmer ID, or a brand-new farmer
  if (!hasId) return <RegisterNew go={go} back={() => setHasId(true)} />;
  return <RegisterWithId go={go} newFarmer={() => setHasId(false)} />;
}

// A new farmer with no department Farmer ID: name, mobile, district and password. The app gives
// them a Farmer ID (not yet verified by the AEO); next they agree to consent and fill in their details.
function RegisterNew({ go, back }) {
  const { te, t, terr } = useLang();
  const [f, setF] = useState({ name: "", mobile: "", district: "", password: "", confirm: "" });
  const [districts, setDistricts] = useState([]);
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const set = (k) => (v) => setF({ ...f, [k]: typeof v === "string" ? v : v.target.value });
  useEffect(() => { api.districts().then(setDistricts).catch(() => {}); }, []);

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      const u = await api.registerNew(f);
      go("login", [`Account created for ${u.name}. Your new Farmer ID is ${u.user_id}. Log in with it or with your mobile number.`,
        `${u.name} గారి ఖాతా తెరవబడింది. మీ కొత్త రైతు ID ${u.user_id}. దీనితో లేదా మీ మొబైల్ నంబర్‌తో లాగిన్ చేయండి.`]);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form onSubmit={submit}>
      <h2>{t("New farmer sign-up", "కొత్త రైతు నమోదు")}</h2>
      <RegisterChoice hasId={false} onChange={back} />
      <p className="muted">{t("No Farmer ID yet? Sign up here. You get a new Farmer ID; your AEO verifies your details later.",
        "రైతు ID ఇంకా లేదా? ఇక్కడ నమోదు చేసుకోండి. మీకు కొత్త రైతు ID వస్తుంది; మీ వివరాలను తర్వాత మీ AEO పరిశీలిస్తారు.")}</p>
      <label>{t("Full name", "పూర్తి పేరు")}</label>
      <input value={f.name} onChange={set("name")} autoComplete="name" required />
      <label>{t("Mobile number", "మొబైల్ నంబర్")}</label>
      <input value={f.mobile} onChange={set("mobile")} inputMode="numeric" maxLength={10} placeholder={t("10-digit mobile", "10 అంకెల మొబైల్ నంబర్")} required />
      <label>{t("District", "జిల్లా")}</label>
      <select value={f.district} onChange={set("district")} required>
        <option value="" disabled>{t("Choose…", "ఎంచుకోండి…")}</option>
        {districts.map((d) => <option key={d.name} value={d.name}>{te ? d.te : d.name}</option>)}
      </select>
      <label>{t("Create password", "పాస్‌వర్డ్ పెట్టుకోండి")}</label>
      <PasswordInput value={f.password} onChange={set("password")} show={show} setShow={setShow} autoComplete="new-password" />
      <Strength password={f.password} />
      <label>{t("Confirm password", "పాస్‌వర్డ్ మళ్లీ రాయండి")}</label>
      <PasswordInput value={f.confirm} onChange={set("confirm")} show={show} setShow={setShow} autoComplete="new-password" />
      {error && <div className="error">{terr(error)}</div>}
      <button className="primary full">{t("Create account", "ఖాతా తెరవండి")}</button>
      <p className="center muted">{t("Already registered?", "ఇప్పటికే ఖాతా ఉందా?")} <a onClick={() => go("login")}>{t("Log in")}</a></p>
    </form>
  );
}

// "I have a Farmer ID" | "New farmer (no Farmer ID)"
function RegisterChoice({ hasId, onChange }) {
  const { t } = useLang();
  return (
    <div className="seg reg-choice">
      <button type="button" className={hasId ? "on" : ""} onClick={() => !hasId && onChange()}>{t("I have a Farmer ID", "నాకు రైతు ID ఉంది")}</button>
      <button type="button" className={hasId ? "" : "on"} onClick={() => hasId && onChange()}>{t("New farmer (no Farmer ID)", "కొత్త రైతు (ID లేదు)")}</button>
    </div>
  );
}

function RegisterWithId({ go, newFarmer }) {
  const { t, terr } = useLang();
  const [f, setF] = useState({ farmer_id: "", mobile: "", password: "", confirm: "" });
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const set = (k) => (v) => setF({ ...f, [k]: typeof v === "string" ? v : v.target.value });

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      const u = await api.register(f);
      go("login", [`Account created for ${u.name}. You can log in with Farmer ID ${u.user_id}.`,
        `${u.name} గారి ఖాతా తెరవబడింది. రైతు ID ${u.user_id} తో లాగిన్ చేయండి.`]);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form onSubmit={submit}>
      <h2>{t("Farmer sign-up", "రైతు నమోదు")}</h2>
      <RegisterChoice hasId onChange={newFarmer} />
      <p className="muted">{t("Use the Farmer ID and mobile number registered with your Agriculture Extension Officer.",
        "మీ వ్యవసాయ విస్తరణ అధికారి (AEO) వద్ద నమోదైన రైతు ID, మొబైల్ నంబర్ వాడండి.")}</p>
      <label>{t("Farmer ID")}</label>
      <input value={f.farmer_id} onChange={set("farmer_id")} placeholder={t("e.g. TS1010", "ఉదా. TS1010")} required />
      <label>{t("Registered mobile number", "నమోదైన మొబైల్ నంబర్")}</label>
      <input value={f.mobile} onChange={set("mobile")} inputMode="numeric" maxLength={10} placeholder={t("10-digit mobile", "10 అంకెల మొబైల్ నంబర్")} required />
      <label>{t("Create password", "పాస్‌వర్డ్ పెట్టుకోండి")}</label>
      <PasswordInput value={f.password} onChange={set("password")} show={show} setShow={setShow} autoComplete="new-password" />
      <Strength password={f.password} />
      <label>{t("Confirm password", "పాస్‌వర్డ్ మళ్లీ రాయండి")}</label>
      <PasswordInput value={f.confirm} onChange={set("confirm")} show={show} setShow={setShow} autoComplete="new-password" />
      {error && <div className="error">{terr(error)}</div>}
      <button className="primary full">{t("Create account", "ఖాతా తెరవండి")}</button>
      <p className="center muted">{t("Already registered?", "ఇప్పటికే ఖాతా ఉందా?")} <a onClick={() => go("login")}>{t("Log in")}</a></p>
      <p className="hint">{t("Demo tip: staff can find farmer IDs and mobile numbers in Farmer Services.",
        "డెమో సూచన: రైతు ID లు, మొబైల్ నంబర్లు సిబ్బంది 'రైతు సేవలు'లో చూడవచ్చు.")}</p>
    </form>
  );
}

function Forgot({ go, onSent }) {
  const { t, terr } = useLang();
  const [userId, setUserId] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const r = await api.forgotPassword({ user_id: userId });
      onSent({ ...r, user_id: userId });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit}>
      <h2>{t("Forgot password", "పాస్‌వర్డ్ మర్చిపోయారా?")}</h2>
      <p className="muted">{t("Enter your user ID. We'll send a 6-digit code to your registered mobile number.",
        "మీ యూజర్ ID రాయండి. మీ నమోదైన మొబైల్ నంబర్‌కు 6 అంకెల కోడ్ పంపుతాం.")}</p>
      <label>{t("User ID / Farmer ID", "యూజర్ ID / రైతు ID")}</label>
      <input value={userId} onChange={(e) => setUserId(e.target.value)} autoFocus required />
      {error && <div className="error">{terr(error)}</div>}
      <button className="primary full" disabled={busy}>{busy ? t("Sending…", "పంపుతున్నాం…") : t("Send code", "కోడ్ పంపండి")}</button>
      <p className="center muted"><a onClick={() => go("login")}>{t("← Back to login", "← లాగిన్‌కు వెనక్కి")}</a></p>
    </form>
  );
}

function Reset({ info, go }) {
  const { te, t, terr } = useLang();
  const [f, setF] = useState({ otp: "", password: "", confirm: "" });
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [sent, setSent] = useState(info);
  const set = (k) => (v) => setF({ ...f, [k]: typeof v === "string" ? v : v.target.value });

  if (!sent) return <Forgot go={go} onSent={setSent} />;

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      await api.resetPassword({ user_id: sent.user_id, ...f });
      go("login", ["Password changed. Please log in with your new password.", "పాస్‌వర్డ్ మారింది. కొత్త పాస్‌వర్డ్‌తో లాగిన్ చేయండి."]);
    } catch (err) {
      setError(err.message);
    }
  }

  async function resend() {
    const r = await api.forgotPassword({ user_id: sent.user_id });
    setSent({ ...r, user_id: sent.user_id });
    setError("");
  }

  return (
    <form onSubmit={submit}>
      <h2>{t("Reset password", "కొత్త పాస్‌వర్డ్ పెట్టండి")}</h2>
      {te ? (
        <p className="muted"><b>{sent.sent_to}</b> కు 6 అంకెల కోడ్ పంపాం. ఇది {sent.expires_in_minutes} నిమిషాల వరకే పనిచేస్తుంది.</p>
      ) : (
        <p className="muted">We sent a 6-digit code to <b>{sent.sent_to}</b>. It expires in {sent.expires_in_minutes} minutes.</p>
      )}
      <div className="demo-otp">
        📱 {t("Demo SMS (no real SMS in this prototype): your code is", "డెమో SMS (ఈ నమూనా యాప్‌లో నిజమైన SMS రాదు): మీ కోడ్")} <b>{sent.demo_otp}</b>
      </div>
      <label>{t("6-digit code", "6 అంకెల కోడ్")}</label>
      <input value={f.otp} onChange={set("otp")} inputMode="numeric" maxLength={6} autoFocus required />
      <label>{t("New password", "కొత్త పాస్‌వర్డ్")}</label>
      <PasswordInput value={f.password} onChange={set("password")} show={show} setShow={setShow} autoComplete="new-password" />
      <Strength password={f.password} />
      <label>{t("Confirm new password", "కొత్త పాస్‌వర్డ్ మళ్లీ రాయండి")}</label>
      <PasswordInput value={f.confirm} onChange={set("confirm")} show={show} setShow={setShow} autoComplete="new-password" />
      {error && <div className="error">{terr(error)}</div>}
      <button className="primary full">{t("Reset password", "పాస్‌వర్డ్ మార్చండి")}</button>
      <p className="center muted"><a onClick={resend}>{t("Resend code", "కోడ్ మళ్లీ పంపండి")}</a> · <a onClick={() => go("login")}>{t("Back to login", "లాగిన్‌కు వెనక్కి")}</a></p>
    </form>
  );
}

export function PasswordInput({ value, onChange, show, setShow, autoComplete }) {
  const { t } = useLang();
  return (
    <div className="pw">
      <input type={show ? "text" : "password"} value={value} onChange={(e) => onChange(e.target.value)} autoComplete={autoComplete} required />
      <button type="button" onClick={() => setShow(!show)} title={show ? t("Hide password", "పాస్‌వర్డ్ దాచండి") : t("Show password", "పాస్‌వర్డ్ చూపించండి")}>{show ? "🙈" : "👁️"}</button>
    </div>
  );
}

export function Strength({ password }) {
  const { t } = useLang();
  const checks = [
    [password.length >= 8, t("8+ characters", "8+ అక్షరాలు")],
    [/[A-Za-z]/.test(password), t("a letter", "ఒక అక్షరం")],
    [/\d/.test(password), t("a number", "ఒక అంకె")],
    [/[^A-Za-z0-9]/.test(password), t("a symbol (recommended)", "@ # వంటి గుర్తు (మంచిది)")],
  ];
  return (
    <div className="strength">
      {checks.map(([ok, label], i) => <span key={i} className={ok ? "ok" : ""}>{ok ? "✓" : "○"} {label}</span>)}
    </div>
  );
}
