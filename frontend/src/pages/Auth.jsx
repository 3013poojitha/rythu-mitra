import { useState } from "react";
import { api, session } from "../api.jsx";

// Login, farmer sign-up, forgot password and reset password - one card that switches between modes
export default function Auth({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [notice, setNotice] = useState("");
  const [resetFor, setResetFor] = useState(null); // {user_id, sent_to, demo_otp}

  const go = (m, msg = "") => {
    setMode(m);
    setNotice(msg);
  };

  return (
    <div className="auth-page">
      <div className="auth-hero">
        <div className="logo big">🌾</div>
        <h1>Rythu Mitra <span className="te">రైతు మిత్ర</span></h1>
        <p>Telangana Agriculture Department × Bharat Vistaar</p>
        <ul>
          <li>Telugu & English farmer assistant</li>
          <li>Crop disease detection with spray guidance</li>
          <li>Scheme, payment and grievance status</li>
          <li>Content pipeline and PMU dashboard for staff</li>
        </ul>
        <small>Prototype with dummy data</small>
      </div>

      <div className="auth-card panel">
        {notice && <div className="success">{notice}</div>}
        {mode === "login" && <Login onLogin={onLogin} go={go} />}
        {mode === "register" && <Register go={go} />}
        {mode === "forgot" && <Forgot go={go} onSent={(r) => { setResetFor(r); go("reset"); }} />}
        {mode === "reset" && <Reset info={resetFor} go={go} />}
      </div>
    </div>
  );
}

function Login({ onLogin, go }) {
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
      <h2>Log in</h2>
      <p className="muted">Farmers use their Farmer ID (e.g. TS1002). Staff use their department user ID.</p>
      <label>User ID</label>
      <input value={userId} onChange={(e) => setUserId(e.target.value)} autoComplete="username" autoFocus required />
      <label>Password</label>
      <PasswordInput value={password} onChange={setPassword} show={show} setShow={setShow} autoComplete="current-password" />
      <div className="row between auth-row">
        <label className="check"><input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} /> Remember me</label>
        <a onClick={() => go("forgot")}>Forgot password?</a>
      </div>
      {error && <div className="error">{error}</div>}
      <button className="primary full" disabled={busy}>{busy ? "Logging in…" : "Log in"}</button>
      <p className="center muted">New farmer? <a onClick={() => go("register")}>Create an account</a></p>
      <details className="demo-accounts">
        <summary>Demo accounts</summary>
        <p>See the <b>Demo accounts</b> table in README.md for the user IDs and passwords of each role (Admin, Contributor, Reviewer, BV Central, Farmer).</p>
      </details>
    </form>
  );
}

function Register({ go }) {
  const [f, setF] = useState({ farmer_id: "", mobile: "", password: "", confirm: "" });
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const set = (k) => (v) => setF({ ...f, [k]: typeof v === "string" ? v : v.target.value });

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      const u = await api.register(f);
      go("login", `Account created for ${u.name}. You can log in with Farmer ID ${u.user_id}.`);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form onSubmit={submit}>
      <h2>Farmer sign-up</h2>
      <p className="muted">Use the Farmer ID and mobile number registered with your Agriculture Extension Officer.</p>
      <label>Farmer ID</label>
      <input value={f.farmer_id} onChange={set("farmer_id")} placeholder="e.g. TS1010" required />
      <label>Registered mobile number</label>
      <input value={f.mobile} onChange={set("mobile")} inputMode="numeric" maxLength={10} placeholder="10-digit mobile" required />
      <label>Create password</label>
      <PasswordInput value={f.password} onChange={set("password")} show={show} setShow={setShow} autoComplete="new-password" />
      <Strength password={f.password} />
      <label>Confirm password</label>
      <PasswordInput value={f.confirm} onChange={set("confirm")} show={show} setShow={setShow} autoComplete="new-password" />
      {error && <div className="error">{error}</div>}
      <button className="primary full">Create account</button>
      <p className="center muted">Already registered? <a onClick={() => go("login")}>Log in</a></p>
      <p className="hint">Demo tip: staff can find farmer IDs and mobile numbers in Farmer Services.</p>
    </form>
  );
}

function Forgot({ go, onSent }) {
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
      <h2>Forgot password</h2>
      <p className="muted">Enter your user ID. We'll send a 6-digit code to your registered mobile number.</p>
      <label>User ID / Farmer ID</label>
      <input value={userId} onChange={(e) => setUserId(e.target.value)} autoFocus required />
      {error && <div className="error">{error}</div>}
      <button className="primary full" disabled={busy}>{busy ? "Sending…" : "Send code"}</button>
      <p className="center muted"><a onClick={() => go("login")}>← Back to login</a></p>
    </form>
  );
}

function Reset({ info, go }) {
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
      go("login", "Password changed. Please log in with your new password.");
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
      <h2>Reset password</h2>
      <p className="muted">We sent a 6-digit code to <b>{sent.sent_to}</b>. It expires in {sent.expires_in_minutes} minutes.</p>
      <div className="demo-otp">📱 Demo SMS (no real SMS in this prototype): your code is <b>{sent.demo_otp}</b></div>
      <label>6-digit code</label>
      <input value={f.otp} onChange={set("otp")} inputMode="numeric" maxLength={6} autoFocus required />
      <label>New password</label>
      <PasswordInput value={f.password} onChange={set("password")} show={show} setShow={setShow} autoComplete="new-password" />
      <Strength password={f.password} />
      <label>Confirm new password</label>
      <PasswordInput value={f.confirm} onChange={set("confirm")} show={show} setShow={setShow} autoComplete="new-password" />
      {error && <div className="error">{error}</div>}
      <button className="primary full">Reset password</button>
      <p className="center muted"><a onClick={resend}>Resend code</a> · <a onClick={() => go("login")}>Back to login</a></p>
    </form>
  );
}

export function PasswordInput({ value, onChange, show, setShow, autoComplete }) {
  return (
    <div className="pw">
      <input type={show ? "text" : "password"} value={value} onChange={(e) => onChange(e.target.value)} autoComplete={autoComplete} required />
      <button type="button" onClick={() => setShow(!show)} title={show ? "Hide password" : "Show password"}>{show ? "🙈" : "👁️"}</button>
    </div>
  );
}

export function Strength({ password }) {
  const checks = [
    [password.length >= 8, "8+ characters"],
    [/[A-Za-z]/.test(password), "a letter"],
    [/\d/.test(password), "a number"],
    [/[^A-Za-z0-9]/.test(password), "a symbol (recommended)"],
  ];
  return (
    <div className="strength">
      {checks.map(([ok, label]) => <span key={label} className={ok ? "ok" : ""}>{ok ? "✓" : "○"} {label}</span>)}
    </div>
  );
}
