import { useState, useEffect } from "react";
import { isLoggedIn, setToken, getToken, clearToken, authFetch } from "./auth.js";

export default function App() {
  const [loggedIn, setLoggedIn] = useState(isLoggedIn());
  const [user, setUser] = useState(null);
  const [health, setHealth] = useState(null);
  const [tables, setTables] = useState([]);
  const [queryResult, setQueryResult] = useState(null);
  const [selectedTable, setSelectedTable] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");

    if (code) {
      fetch(`/auth/callback?code=${code}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.access_token) {
            setToken(data.access_token);
            setLoggedIn(true);
            window.history.replaceState({}, "", "/");
          }
        })
        .catch((e) => setError(e.message));
    }
  }, []);

  useEffect(() => {
    if (loggedIn) {
      authFetch("/auth/me")
        .then(setUser)
        .catch(() => {
          clearToken();
          setLoggedIn(false);
        });
    }
  }, [loggedIn]);

  async function handleLogin() {
    try {
      const res = await fetch("/auth/login");
      const data = await res.json();
      window.location.href = data.login_url;
    } catch (e) {
      setError(e.message);
    }
  }

  function handleLogout() {
    clearToken();
    setUser(null);
    setLoggedIn(false);
  }

  async function checkHealth() {
    setError(null);
    try { setHealth(await authFetch("/health/db")); }
    catch (e) { setError(e.message); }
  }

  async function fetchTables() {
    setError(null);
    try { setTables((await authFetch("/api/tables")).tables || []); }
    catch (e) { setError(e.message); }
  }

  async function fetchData() {
    if (!selectedTable) return;
    setError(null); setLoading(true);
    try { setQueryResult(await authFetch(`/api/query?table=${selectedTable}&limit=10`)); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }

  const btn = { padding: "8px 16px", marginRight: 8, cursor: "pointer" };
  const pre = { background: "#f4f4f4", padding: 12, borderRadius: 6, marginTop: 8 };
  const th = { border: "1px solid #ccc", padding: 8, background: "#f0f0f0", textAlign: "left" };
  const td = { border: "1px solid #ccc", padding: 8 };

  if (!loggedIn) {
    return (
      <div style={{ fontFamily: "sans-serif", maxWidth: 400, margin: "100px auto", textAlign: "center" }}>
        <h1>SPCS App</h1>
        <p style={{ color: "#666" }}>Sign in to continue</p>
        {error && <div style={{ background: "#fee", border: "1px solid #c00", padding: 12, borderRadius: 6, marginBottom: 16 }}>{error}</div>}
        <button onClick={handleLogin} style={{ ...btn, padding: "12px 32px", fontSize: 16 }}>
          Sign in with SSO
        </button>
      </div>
    );
  }

  return (
    <div style={{ fontFamily: "sans-serif", maxWidth: 900, margin: "40px auto", padding: "0 20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>SPCS App</h1>
        <div>
          <span style={{ marginRight: 12, color: "#666" }}>{user?.email || ""}</span>
          <button onClick={handleLogout} style={btn}>Logout</button>
        </div>
      </div>

      {error && <div style={{ background: "#fee", border: "1px solid #c00", padding: 12, borderRadius: 6, marginBottom: 16 }}>{error}</div>}

      <section style={{ marginBottom: 24 }}>
        <h2>1. Health check</h2>
        <button onClick={checkHealth} style={btn}>Check DB</button>
        {health && <pre style={pre}>{JSON.stringify(health, null, 2)}</pre>}
      </section>

      <section style={{ marginBottom: 24 }}>
        <h2>2. Tables</h2>
        <button onClick={fetchTables} style={btn}>Load tables</button>
        {tables.length > 0 && (
          <select value={selectedTable} onChange={(e) => setSelectedTable(e.target.value)} style={{ marginLeft: 8, padding: 6 }}>
            <option value="">-- select --</option>
            {tables.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        )}
      </section>

      <section>
        <h2>3. Query data</h2>
        <button onClick={fetchData} disabled={!selectedTable || loading} style={btn}>{loading ? "Loading..." : "Fetch data"}</button>
        {queryResult && (
          <div style={{ overflowX: "auto", marginTop: 12 }}>
            <p>{queryResult.count} rows</p>
            <table style={{ borderCollapse: "collapse", width: "100%" }}>
              <thead><tr>{queryResult.columns.map((c) => <th key={c} style={th}>{c}</th>)}</tr></thead>
              <tbody>{queryResult.rows.map((row, i) => (
                <tr key={i}>{queryResult.columns.map((c) => <td key={c} style={td}>{String(row[c] ?? "")}</td>)}</tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}