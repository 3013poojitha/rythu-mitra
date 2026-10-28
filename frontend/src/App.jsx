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
import History from "./pages/History.jsx";
import WhatsAppButton from "./WhatsAppButton.jsx";
import Bell from "./Bell.jsx";
import { LangSwitch, useLang } from "./i18n.jsx";

const START_HASH = location.hash; // remembered before the app rewrites it
const STAFF = ["admin", "contributor", "reviewer", "bv_central"];
// Labels are [English, Telugu]; staff-only tabs stay English
const TABS = [
  // Farmers chat on My Details (under their details); the chat tab is for staff testing
  { id: "chat", label: ["Farmer Chat", "రైతు చాట్"], sub: ["Stage 1 · Channels", "దశ 1 · చాట్ ఛానెళ్లు"], Page: Chat, roles: STAFF },
  { id: "doctor", label: ["Crop Doctor", "పంట వైద్యుడు"], sub: ["Disease & spray guide", "తెగులు & మందుల సలహా"], Page: CropDoctor },
  { id: "services", label: ["Farmer Services", "రైతు సేవలు"], sub: ["Stage 3 · 4", "దశ 3 · 4"], Page: Services,
    farmerLabel: ["🏠 My Details", "🏠 నా వివరాలు"], farmerSub: ["Details, chat & schemes", "వివరాలు, చాట్ & పథకాలు"] },
  { id: "compare", label: "Claude vs ChatGPT", sub: "Model testing", Page: Compare, roles: STAFF },
  { id: "pipeline", label: "Content Pipeline", sub: "Stage 2", Page: Pipeline, roles: STAFF },
  { id: "dashboard", label: "PMU Dashboard", sub: "Governance", Page: Dashboard, roles: STAFF },
];

export default function App() {
  const { te, t, tv, loadCrops } = useLang();
  const tt = (pair) => (Array.isArray(pair) ? t(pair[0], pair[1]) : pair);
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [tab, setTab] = useState(() => location.hash.slice(1) || "chat");

  // Farmers start on their own details; staff start on the chat
  function onLogin(u) {
    setUser(u);
    setTab(u.role === "farmer" ? "services" : "chat");
  }
  const [status, setStatus] = useState(null);
  const [menu, setMenu] = useState(false);
  const [askLogout, setAskLogout] = useState(false); // "Do you want to log out?" box
  const [waOpen, setWaOpen] = useState(0); // goes up each time the floating WhatsApp button is tapped

  useEffect(() => {
    session.onExpired(() => setUser(null));
    api.status().then(setStatus).catch(() => setStatus({ error: true }));
    // Restore a saved login, if any
    if (session.get()) api.me().then((u) => { setUser(u); if (!START_HASH && u.role === "farmer") setTab("services"); }).catch(() => {}).finally(() => setChecking(false));
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

  useEffect(() => {
    if (user) loadCrops(); // Telugu crop names
  }, [user?.user_id]);

  async function logout() {
    await api.logout().catch(() => {});
    session.clear();
    setUser(null);
    setMenu(false);
    setAskLogout(false);
  }

  if (checking) return <div className="center pad">{t("Loading…", "లోడ్ అవుతోంది…")}</div>;
  if (!user) return <Auth onLogin={onLogin} />;

  const isFarmer = user.role === "farmer";
  const tabs = TABS.filter((x) => !x.roles || x.roles.includes(user.role))
    .sort((a, b) => (isFarmer ? (b.id === "services") - (a.id === "services") : 0));
  // Change password, History and How the app works open from the user menu (top right), not the tab bar
  const MENU_PAGES = { password: ChangePassword, history: History, about: About };
  const { Page } = MENU_PAGES[tab] ? { Page: MENU_PAGES[tab] } : tabs.find((x) => x.id === tab) || tabs[0];
  const anyMock = status?.providers && Object.values(status.providers).some((p) => p.mode === "mock");

  return (
    <div className="app">
      {/* App name, user menu and tabs stay at the top while the page scrolls */}
      <div className="sticky-head">
      <header className="topbar">
        <div className="brand">
          <div className="logo">🌾</div>
          <div>
            <div className="brand-title">{te ? "రైతు మిత్ర" : "Rythu Mitra"}</div>
            <div className="brand-sub">{t("Telangana Agriculture Dept × Bharat Vistaar")} · {t("Prototype with dummy data")}</div>
          </div>
        </div>
        <div className="status">
          {/* Mock / Live AI is shown in the yellow line under the tabs, not here */}
          <LangSwitch className="on-dark" />
          {user.role === "farmer" && <Bell refresh={tab} />}
          <div className="user-menu">
            <button className="user-btn" onClick={() => setMenu(!menu)}>
              <span className="initial">{user.name[0]}</span>
              <span className="who"><b>{user.name}</b><small>{tv(user.role_label)}</small></span> ▾
            </button>
            {menu && (
              <div className="dropdown" onMouseLeave={() => setMenu(false)}>
                <div className="dd-head"><b>{user.user_id}</b><small>{t("Mobile")} {user.mobile_masked}</small></div>
                <button onClick={() => { setTab("password"); setMenu(false); }}>🔑 {t("Change password")}</button>
                <button onClick={() => { setTab("history"); setMenu(false); }}>
                  📜 {user.role === "farmer" ? t("My history") : t("Crop history", "పంట చరిత్ర")}
                </button>
                <button onClick={() => { setTab("about"); setMenu(false); }}>{t("How the app works")}</button>
                <button onClick={() => { setAskLogout(true); setMenu(false); }}>🚪 {t("Log out")}</button>
              </div>
            )}
          </div>
        </div>
      </header>
      <nav className="tabs">
        {tabs.map((x) => (
          <button key={x.id} className={x.id === tab ? "tab active" : "tab"} onClick={() => { setTab(x.id); setWaOpen(0); }}>
            <span>{tt(isFarmer && x.farmerLabel ? x.farmerLabel : x.label)}</span>
            <small>{tt(isFarmer && x.farmerSub ? x.farmerSub : x.sub)}</small>
          </button>
        ))}
      </nav>
      </div>
      {anyMock && tab !== "about" && (
        <div className="banner">
          {te ? (
            <>యాప్ ఇప్పుడు <b>మాక్ AI మోడ్</b>‌లో నడుస్తోంది — API కీలు అవసరం లేదు. జవాబులు నమూనా సమాచారం నుండి వస్తాయి; AI జవాబులు అనుకరణ మాత్రమే.</>
          ) : (
            <>Running in <b>Mock AI mode</b> — no API keys needed. Answers come from dummy data with simulated model replies.</>
          )}{" "}
          <a onClick={() => setTab("about")}>{t("What does this mean?", "దీని అర్థం ఏమిటి?")}</a>
        </div>
      )}
      <main className="content">
        <Page user={user} refreshUser={() => api.me().then(setUser).catch(() => {})} waOpen={waOpen}
              goHome={() => setTab(isFarmer ? "services" : "chat")} />
      </main>
      <WhatsAppButton label={t("Chat on WhatsApp", "వాట్సాప్‌లో మాట్లాడండి")}
                      onOpen={() => { setTab(isFarmer ? "services" : "chat"); setWaOpen((n) => n + 1); }} />
      {askLogout && (
        <div className="modal-bg" onClick={() => setAskLogout(false)}>
          <div className="panel modal confirm" onClick={(e) => e.stopPropagation()}>
            <div className="confirm-icon">🚪</div>
            <h2>{t("Log out?", "లాగ్ అవుట్ అవ్వాలా?")}</h2>
            <p className="muted">{t("Do you want to log out of Rythu Mitra?", "మీరు రైతు మిత్ర నుండి లాగ్ అవుట్ అవ్వాలనుకుంటున్నారా?")}</p>
            <div className="row gap-sm end">
              <button onClick={() => setAskLogout(false)} autoFocus>{t("Cancel", "రద్దు చేయండి")}</button>
              <button className="primary" onClick={logout}>{t("Log out")}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Change password: its own page, opened from the user menu like My history
function ChangePassword({ goHome }) {
  const { t, terr } = useLang();
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
    <div className="pw-page">
      <form className="panel" onSubmit={submit}>
        <div className="row between">
          <h2>🔑 {t("Change password")}</h2>
          <button type="button" onClick={goHome}>← {t("Back", "వెనక్కి")}</button>
        </div>
        <p className="muted">{t("Passwords need 8 or more characters, with letters and numbers.", "పాస్‌వర్డ్‌లో కనీసం 8 అక్షరాలు ఉండాలి — అక్షరాలు, అంకెలు రెండూ.")}</p>
        {done ? (
          <>
            <div className="success">{t("Password changed successfully.", "పాస్‌వర్డ్ మారింది.")}</div>
            <div className="row gap-sm">
              <button type="button" className="primary" onClick={goHome}>🏠 {t("Back to main page", "ముఖ్య పేజీకి వెళ్ళండి")}</button>
              <button type="button" onClick={() => { setDone(false); setF({ current: "", password: "", confirm: "" }); }}>{t("Change it again", "మళ్లీ మార్చండి")}</button>
            </div>
          </>
        ) : (
          <>
            <label>{t("Current password", "ప్రస్తుత పాస్‌వర్డ్")}</label>
            <PasswordInput value={f.current} onChange={set("current")} show={show} setShow={setShow} autoComplete="current-password" />
            <label>{t("New password", "కొత్త పాస్‌వర్డ్")}</label>
            <PasswordInput value={f.password} onChange={set("password")} show={show} setShow={setShow} autoComplete="new-password" />
            <Strength password={f.password} />
            <label>{t("Confirm new password", "కొత్త పాస్‌వర్డ్ మళ్లీ రాయండి")}</label>
            <PasswordInput value={f.confirm} onChange={set("confirm")} show={show} setShow={setShow} autoComplete="new-password" />
            {error && <div className="error">{terr(error)}</div>}
            <div className="row gap-sm">
              <button className="primary">💾 {t("Save")}</button>
              <button type="button" onClick={goHome}>🏠 {t("Back to main page", "ముఖ్య పేజీకి వెళ్ళండి")}</button>
            </div>
          </>
        )}
      </form>
    </div>
  );
}
