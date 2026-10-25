import { useEffect, useState } from "react";
import { api } from "../api.jsx";

const ROLES = [
  { id: "contributor", label: "Contributor (NISG)" },
  { id: "reviewer", label: "Reviewer (Agri Dept)" },
  { id: "bv_central", label: "Bharat Vistaar central team" },
  { id: "admin", label: "Admin (can do any step)" },
];
const ACTOR_LABEL = { system: "Platform (automatic)", contributor: "Contributor", reviewer: "Reviewer", bv_central: "BV central team" };

export default function Pipeline({ user }) {
  const isAdmin = user.role === "admin";
  const [stages, setStages] = useState([]);
  const [docs, setDocs] = useState([]);
  // Users act in their own role; only an admin can switch roles to demo the whole flow
  const [role, setRole] = useState(user.role);
  const [selected, setSelected] = useState(null);
  const [view, setView] = useState("translation");
  const [error, setError] = useState("");
  const [showUpload, setShowUpload] = useState(false);

  const load = () => api.documents().then((d) => {
    setDocs(d);
    setSelected((s) => (s ? d.find((x) => x.id === s.id) : d[0]));
  });
  useEffect(() => {
    api.stages().then(setStages);
    load();
  }, []);

  async function advance(doc) {
    setError("");
    try {
      const updated = await api.advance(doc.id, role);
      setDocs((ds) => ds.map((d) => (d.id === updated.id ? updated : d)));
      setSelected(updated);
    } catch (e) {
      setError(e.message);
    }
  }

  const canAct = (d) => d.next_actor && (role === "admin" || d.next_actor === "system" || d.next_actor === role);

  return (
    <div className="stack">
      <div className="panel">
        <div className="row between">
          <div>
            <h2>Bharat Vistaar content ingestion pipeline</h2>
            <p className="muted">Proposal §2.4 — State circulars move through 11 stages. Only <b>Completed</b> documents are used by the chatbot. Try publishing the Rabi advisory, then ask the chatbot "When to sow Bengal gram?"</p>
          </div>
          <div className="row gap-sm">
            {isAdmin ? (
              <select value={role} onChange={(e) => setRole(e.target.value)}>
                {ROLES.map((r) => <option key={r.id} value={r.id}>Acting as: {r.label}</option>)}
              </select>
            ) : (
              <span className="pill green">Your role: {user.role_label}</span>
            )}
            {(isAdmin || user.role === "contributor") && (
              <button className="primary" onClick={() => setShowUpload(!showUpload)}>+ Upload document</button>
            )}
          </div>
        </div>
        {showUpload && <Upload onDone={(d) => { setShowUpload(false); load().then(() => setSelected(d)); }} />}
      </div>

      <div className="pipe-layout">
        <div className="panel doc-list">
          {docs.map((d) => (
            <div key={d.id} className={`doc-item ${selected?.id === d.id ? "sel" : ""}`} onClick={() => setSelected(d)}>
              <div className="doc-title">{d.title}</div>
              <div className="progress"><div style={{ width: `${(d.stage / (stages.length - 1 || 1)) * 100}%` }} /></div>
              <div className="row between">
                <small className={d.stage === stages.length - 1 ? "ok" : ""}>{d.stage_label}</small>
                <small className="muted">{d.category} · {d.source_lang === "te" ? "Telugu" : "English"}</small>
              </div>
            </div>
          ))}
        </div>

        {selected && (
          <div className="panel">
            <h3>{selected.title}</h3>
            <ol className="stepper">
              {stages.map((s, i) => (
                <li key={s.key} className={i < selected.stage ? "done" : i === selected.stage ? "current" : ""}>
                  <span className="dot">{i < selected.stage || i === stages.length - 1 && i === selected.stage ? "✓" : i + 1}</span>
                  <span className="lbl">{s.label}<small>{s.actor ? ACTOR_LABEL[s.actor] : ""}</small></span>
                </li>
              ))}
            </ol>

            {selected.next_actor ? (
              <div className="action-box">
                <div>
                  Next step: <b>{selected.next_label}</b> — done by <b>{ACTOR_LABEL[selected.next_actor]}</b>
                </div>
                <button className="primary" disabled={!canAct(selected)} onClick={() => advance(selected)}>
                  {selected.next_actor === "system" ? "Run platform step" : `Approve as ${ACTOR_LABEL[selected.next_actor]}`}
                </button>
                {!canAct(selected) && (
                  <small className="muted">
                    {isAdmin ? `Switch "Acting as" to ${ACTOR_LABEL[selected.next_actor]} to continue.` : `Waiting for the ${ACTOR_LABEL[selected.next_actor]} — log in with that account to continue.`}
                  </small>
                )}
              </div>
            ) : (
              <div className="action-box ok">✅ Live in production — farmers can now get answers from this document.</div>
            )}
            {error && <div className="error">{error}</div>}

            <div className="seg small">
              {[["original", "Original"], ["translation", "English translation"], ["chunks", `Knowledge chunks (${selected.chunks.length})`], ["history", "Audit trail"]].map(([k, l]) => (
                <button key={k} className={view === k ? "on" : ""} onClick={() => setView(k)}>{l}</button>
              ))}
            </div>
            <div className="doc-body">
              {view === "original" && <pre>{selected.raw_text}</pre>}
              {view === "translation" && <pre>{selected.translation || "Not translated yet — run the 'Translating' step."}</pre>}
              {view === "chunks" && (selected.chunks.length ? selected.chunks.map((c) => (
                <div key={c.id} className="chunk"><span className={`pill ${c.approved ? "green" : "amber"}`}>{c.approved ? "Approved" : "Pending"}</span> {c.text}</div>
              )) : <p className="muted">Chunks are created at the 'Approve content' stage.</p>)}
              {view === "history" && (
                <table><thead><tr><th>Stage</th><th>By</th><th>When</th><th>Note</th></tr></thead>
                  <tbody>{selected.history.map((h, i) => <tr key={i}><td>{h.stage}</td><td>{h.by}</td><td>{h.at.replace("T", " ")}</td><td>{h.note}</td></tr>)}</tbody>
                </table>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Upload({ onDone }) {
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("Circular");
  const [lang, setLang] = useState("te");
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [err, setErr] = useState("");

  async function submit() {
    const f = new FormData();
    f.append("title", title || "Untitled document");
    f.append("category", category);
    f.append("lang", lang);
    f.append("text", text);
    if (file) f.append("file", file);
    try {
      onDone(await api.uploadDocument(f));
    } catch (e) {
      setErr(e.message);
    }
  }

  return (
    <div className="upload">
      <div className="row gap-sm wrap">
        <input className="grow" placeholder="Document title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          {["Circular", "Scheme guideline", "Advisory", "Notification"].map((c) => <option key={c}>{c}</option>)}
        </select>
        <select value={lang} onChange={(e) => setLang(e.target.value)}>
          <option value="te">Telugu</option><option value="en">English</option>
        </select>
      </div>
      <textarea rows={5} placeholder="Paste the document text here, or choose a .txt / .pdf file below" value={text} onChange={(e) => setText(e.target.value)} />
      <div className="row between">
        <input type="file" accept=".txt,.pdf" onChange={(e) => setFile(e.target.files[0])} />
        <button className="primary" onClick={submit}>Upload as Contributor</button>
      </div>
      {err && <div className="error">{err}</div>}
    </div>
  );
}
