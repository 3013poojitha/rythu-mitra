import { useEffect, useState } from "react";
import { api, session } from "./api.jsx";
import Auth, { PasswordInput, Strength } from "./pages/Auth.jsx";
import Chat from "./pages/Chat.jsx";
import CropDoctor from "./pages/CropDoctor.jsx";
import Compare from "./pages/Compare.jsx";
import Pipeline from "./pages/Pipeline.jsx";
import Services from "./pages/Services.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import About from "./pages/About.jsx";

const STAFF = ["admin", "contributor", "reviewer", "bv_central"];
const TABS = [
  { id: "chat", label: "Farmer Chat", sub: "Stage 1 · Channels", Page: Chat },
  { id: "doctor", label: "Crop Doctor", sub: "Disease & spray guide", Page: CropDoctor },
  { id: "services", label: "Farmer Services", sub: "Stage 3 · 4", Page: Services, farmerLabel: "My Details" },
  { id: "compare", label: "Claude vs ChatGPT", sub: "Model testing", Page: Compare, roles: STAFF },
  { id: "pipeline", label: "Content Pipeline", sub: "Stage 2", Page: Pipeline, roles: STAFF },
  { id: "dashboard", label: "PMU Dashboard", sub: "Governance", Page: Dashboard, roles: STAFF },
  { id: "about", label: "How it works", sub: "Mock AI", Page: About },
];

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [tab, setTab] = useState(() => location.hash.slice(1) || "chat");
  const [status, setStatus] = useState(null);
  const [menu, setMenu] = useState(false);
  const [changePw, setChangePw] = useState(false);

  useEffect(() => {
    session.onExpired(() => setUser(null));
    api.status().then(setStatus).catch(() => setStatus({ error: true }));
    // Restore a saved login, if any
    if (session.get()) api.me().then(setUser).catch(() => {}).finally(() => setChecking(false));
    else setChecking(false);
  }, []);
  useEffect(() => {
    if (location.hash.slice(1) !== tab) location.hash = tab;
  }, [tab]);
  useEffect(() => {
    // Keep the tab in sync with the URL so links and the back button work
    const onHash = () => setTab(location.hash.slice(1) || "chat");
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  async function logout() {
    await api.logout().catch(() => {});
    session.clear();
    setUser(null);
    setMenu(false);
  }

  if (checking) return <div className="center pad">Loading…</div>;
  if (!user) return <Auth onLogin={setUser} />;

  const tabs = TABS.filter((t) => !t.roles || t.roles.includes(user.role));
  const { Page } = tabs.find((t) => t.id === tab) || tabs[0];
  const anyMock = status?.providers && Object.values(status.providers).some((p) => p.mode === "mock");

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="logo">🌾</div>
          <div>
            <div className="brand-title">Rythu Mitra <span className="te">రైతు మిత్ర</span></div>
            <div className="brand-sub">Telangana Agriculture Dept × Bharat Vistaar · Prototype with dummy data</div>
          </div>
        </div>
        <div className="status">
          {status?.providers &&
            Object.entries(status.providers).map(([k, p]) => (
              <span key={k} className={`pill ${p.mode === "live" ? "green" : "amber"}`} title={p.model}>
                {p.label}: {p.mode === "live" ? "Live" : "Mock AI"}
              </span>
            ))}
          <div className="user-menu">
            <button className="user-btn" onClick={() => setMenu(!menu)}>
              <span className="initial">{user.name[0]}</span>
              <span className="who"><b>{user.name}</b><small>{user.role_label}</small></span> ▾
            </button>
            {menu && (
              <div className="dropdown" onMouseLeave={() => setMenu(false)}>
                <div className="dd-head"><b>{user.user_id}</b><small>Mobile {user.mobile_masked}</small></div>
                <button onClick={() => { setChangePw(true); setMenu(false); }}>🔑 Change password</button>
                <button onClick={logout}>🚪 Log out</button>
              </div>
            )}
          </div>
        </div>
      </header>
      <nav className="tabs">
        {tabs.map((t) => (
          <button key={t.id} className={t.id === tab ? "tab active" : "tab"} onClick={() => setTab(t.id)}>
            <span>{user.role === "farmer" && t.farmerLabel ? t.farmerLabel : t.label}</span>
            <small>{t.sub}</small>
          </button>
        ))}
      </nav>
      {anyMock && tab !== "about" && (
        <div className="banner">
          Running in <b>Mock AI mode</b> — no API keys needed. Answers come from dummy data with simulated model replies.{" "}
          <a onClick={() => setTab("about")}>What does this mean?</a>
        </div>
      )}
      <main className="content">
        <Page user={user} />
      </main>
      {changePw && <ChangePassword onClose={() => setChangePw(false)} />}
    </div>
  );
}

function ChangePassword({ onClose }) {
  const [f, setF] = useState({ current: "", password: "", confirm: "" });
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const set = (k) => (v) => setF({ ...f, [k]: v });

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      await api.changePassword(f);
      setDone(true);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="modal-bg" onClick={onClose}>
      <form className="panel modal" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <h2>Change password</h2>
        {done ? (
          <>
            <div className="success">Password changed successfully.</div>
            <button type="button" className="primary full" onClick={onClose}>Close</button>
          </>
        ) : (
          <>
            <label>Current password</label>
            <PasswordInput value={f.current} onChange={set("current")} show={show} setShow={setShow} autoComplete="current-password" />
            <label>New password</label>
            <PasswordInput value={f.password} onChange={set("password")} show={show} setShow={setShow} autoComplete="new-password" />
            <Strength password={f.password} />
            <label>Confirm new password</label>
            <PasswordInput value={f.confirm} onChange={set("confirm")} show={show} setShow={setShow} autoComplete="new-password" />
            {error && <div className="error">{error}</div>}
            <div className="row gap-sm end">
              <button type="button" onClick={onClose}>Cancel</button>
              <button className="primary">Save</button>
            </div>
          </>
        )}
      </form>
    </div>
  );
}
