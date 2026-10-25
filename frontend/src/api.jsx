// Login token: kept in localStorage when "Remember me" is ticked, otherwise only for this tab
const TOKEN_KEY = "rythu_token";
let onUnauthorized = () => {};

function store(remember) {
  try {
    return remember ? localStorage : sessionStorage;
  } catch {
    return null;
  }
}

export const session = {
  get() {
    try {
      return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set(token, remember) {
    session.clear();
    try {
      store(remember)?.setItem(TOKEN_KEY, token);
    } catch {
      /* storage blocked - the user just has to log in again on reload */
    }
  },
  clear() {
    try {
      sessionStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(TOKEN_KEY);
    } catch {
      /* ignore */
    }
  },
  onExpired(fn) {
    onUnauthorized = fn;
  },
};

async function request(path, options = {}) {
  const token = session.get();
  const headers = { ...(options.headers || {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  const res = await fetch(`/api${path}`, { ...options, headers });
  const body = await res.json().catch(() => ({}));
  if (res.status === 401 && token && !path.startsWith("/auth/login")) {
    session.clear();
    onUnauthorized();
  }
  if (!res.ok) throw new Error(body.detail || `Request failed (${res.status})`);
  return body;
}

const json = (method, data) => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(data),
});

export const api = {
  login: (data) => request("/auth/login", json("POST", data)),
  logout: () => request("/auth/logout", { method: "POST" }),
  me: () => request("/auth/me"),
  register: (data) => request("/auth/register", json("POST", data)),
  forgotPassword: (data) => request("/auth/forgot-password", json("POST", data)),
  resetPassword: (data) => request("/auth/reset-password", json("POST", data)),
  changePassword: (data) => request("/auth/change-password", json("POST", data)),
  diseases: () => request("/diseases"),
  status: () => request("/status"),
  chat: (data) => request("/chat", json("POST", data)),
  compare: (data) => request("/compare", json("POST", data)),
  diagnose: (form) => request("/diagnose", { method: "POST", body: form }),
  evaluate: () => request("/evaluate", { method: "POST" }),
  farmers: () => request("/farmers"),
  farmer: (id) => request(`/farmers/${id}`),
  grievances: () => request("/grievances"),
  createGrievance: (data) => request("/grievances", json("POST", data)),
  stages: () => request("/pipeline/stages"),
  documents: () => request("/documents"),
  uploadDocument: (form) => request("/documents", { method: "POST", body: form }),
  advance: (id, role) => request(`/documents/${id}/advance`, json("POST", { role })),
  reference: () => request("/reference"),
  dashboard: () => request("/dashboard"),
};

// Render the small subset of markdown the bot uses: **bold** and line breaks
export function renderText(text) {
  return text.split("\n").map((line, i) => {
    const parts = line.split(/\*\*(.+?)\*\*/g).map((p, j) => (j % 2 ? <strong key={j}>{p}</strong> : p));
    return <div key={i} className={line.trim() ? "" : "spacer"}>{parts}</div>;
  });
}
