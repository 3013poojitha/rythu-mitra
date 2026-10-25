import { Fragment, useState } from "react";
import { api, renderText } from "../api.jsx";

const SAMPLES = [
  "What is the price of chilli today?",
  "రైతు భరోసా పథకం గురించి చెప్పండి",
  "My cotton flowers look like rosettes, what is it?",
  "Will it rain in Nizamabad this week?",
];

export default function Compare() {
  const [q, setQ] = useState(SAMPLES[0]);
  const [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false);
  const [evalRes, setEvalRes] = useState(null);
  const [evalBusy, setEvalBusy] = useState(false);
  const [open, setOpen] = useState(null);

  async function run(question = q) {
    setQ(question);
    setBusy(true);
    try {
      setRes(await api.compare({ message: question }));
    } finally {
      setBusy(false);
    }
  }

  async function runEval() {
    setEvalBusy(true);
    try {
      setEvalRes(await api.evaluate());
    } finally {
      setEvalBusy(false);
    }
  }

  return (
    <div className="stack">
      <div className="panel">
        <h2>Side-by-side: Claude vs ChatGPT</h2>
        <p className="muted">The same question and the same retrieved facts go to both models. Compare tone, accuracy, speed and length.</p>
        <div className="row">
          <input className="grow" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && run()} />
          <button className="primary" onClick={() => run()} disabled={busy}>{busy ? "Asking both…" : "Compare"}</button>
        </div>
        <div className="quick inline">
          {SAMPLES.map((s) => <button key={s} onClick={() => run(s)}>{s}</button>)}
        </div>
      </div>

      {res && (
        <>
          <div className="row gap-sm">
            <span className="tag stage">{res.stage}</span>
            <span className="tag">Intent: {res.intent}</span>
            {res.sources.map((s) => <span key={s} className="tag">{s}</span>)}
          </div>
          <div className="grid2">
            {Object.entries(res.results).map(([p, r]) => (
              <div key={p} className={`panel model-card ${p}`}>
                <div className="model-head">
                  <h3>{p === "claude" ? "Claude" : "ChatGPT"}</h3>
                  <span className={`pill ${r.mode === "live" ? "green" : "amber"}`}>{r.model}</span>
                </div>
                <div className="answer">{renderText(r.text)}</div>
                <div className="stats">
                  <div><b>{r.latency_ms}</b><small>ms latency</small></div>
                  <div><b>{r.tokens_in}</b><small>input tokens</small></div>
                  <div><b>{r.tokens_out}</b><small>output tokens</small></div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="panel">
        <div className="row between">
          <div>
            <h2>Agreed test scenarios</h2>
            <p className="muted">Proposal §2.9: continuously test the bot against agreed scenarios. Each answer must contain the expected facts in the right language.</p>
          </div>
          <button className="primary" onClick={runEval} disabled={evalBusy}>{evalBusy ? "Running…" : "Run all tests"}</button>
        </div>
        {evalRes && (
          <>
            <div className="grid2 small-gap">
              {Object.entries(evalRes.summary).map(([p, s]) => (
                <div key={p} className="score">
                  <b>{p === "claude" ? "Claude" : "ChatGPT"}</b>
                  <span className="big">{s.passed}/{s.total}</span>
                  <small>passed · avg {s.avg_latency_ms} ms</small>
                </div>
              ))}
            </div>
            <table>
              <thead><tr><th>#</th><th>Question</th><th>Expected</th><th>Claude</th><th>ChatGPT</th></tr></thead>
              <tbody>
                {evalRes.results.map((r) => (
                  <Fragment key={r.id}>
                    <tr className="clickable" onClick={() => setOpen(open === r.id ? null : r.id)}>
                      <td>{r.id}</td><td>{r.question}</td><td>{r.expect.join(", ")}</td>
                      {["claude", "gpt"].map((p) => (
                        <td key={p}><span className={`pill ${r.results[p].pass ? "green" : "red"}`}>{r.results[p].pass ? "Pass" : "Fail"}</span> <small>{r.results[p].latency_ms} ms</small></td>
                      ))}
                    </tr>
                    {open === r.id && (
                      <tr><td colSpan={5}><div className="grid2">
                        {["claude", "gpt"].map((p) => <div key={p} className="answer small">{renderText(r.results[p].text)}</div>)}
                      </div></td></tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>
    </div>
  );
}
