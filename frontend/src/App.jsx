import { useState } from "react";

const API = import.meta.env.VITE_API_URL || "";

export default function App() {
  const [health, setHealth] = useState(null);
  const [dbHealth, setDbHealth] = useState(null);
  const [tables, setTables] = useState([]);
  const [queryResult, setQueryResult] = useState(null);
  const [selectedTable, setSelectedTable] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function callApi(path) {
    const res = await fetch(`${API}${path}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Request failed");
    }
    return res.json();
  }

  async function checkHealth() {
    setError(null);
    try {
      const data = await callApi("/health");
      setHealth(data);
    } catch (e) {
      setError(e.message);
    }
  }

  async function checkDbHealth() {
    setError(null);
    try {
      const data = await callApi("/health/db");
      setDbHealth(data);
    } catch (e) {
      setError(e.message);
    }
  }

  async function fetchTables() {
    setError(null);
    try {
      const data = await callApi("/api/tables");
      setTables(data.tables || []);
    } catch (e) {
      setError(e.message);
    }
  }

  async function fetchData() {
    if (!selectedTable) return;
    setError(null);
    setLoading(true);
    try {
      const data = await callApi(`/api/query?table=${selectedTable}&limit=10`);
      setQueryResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ fontFamily: "sans-serif", maxWidth: 900, margin: "40px auto", padding: "0 20px" }}>
      <h1>SPCS App</h1>
      <p style={{ color: "#666" }}>Frontend → Backend → Snowflake Database</p>

      {error && (
        <div style={{ background: "#fee", border: "1px solid #c00", padding: 12, borderRadius: 6, marginBottom: 16 }}>
          {error}
        </div>
      )}

      {/* Health Checks */}
      <section style={{ marginBottom: 24 }}>
        <h2>1. Health Checks</h2>
        <button onClick={checkHealth} style={btn}>Check Backend Health</button>
        {health && <pre style={pre}>{JSON.stringify(health, null, 2)}</pre>}

        <button onClick={checkDbHealth} style={btn}>Check DB Connection</button>
        {dbHealth && <pre style={pre}>{JSON.stringify(dbHealth, null, 2)}</pre>}
      </section>

      {/* Tables */}
      <section style={{ marginBottom: 24 }}>
        <h2>2. Tables</h2>
        <button onClick={fetchTables} style={btn}>Load Tables</button>
        {tables.length > 0 && (
          <select
            value={selectedTable}
            onChange={(e) => setSelectedTable(e.target.value)}
            style={{ marginLeft: 8, padding: 6 }}
          >
            <option value="">-- select table --</option>
            {tables.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        )}
      </section>

      {/* Query */}
      <section>
        <h2>3. Query Data</h2>
        <button onClick={fetchData} disabled={!selectedTable || loading} style={btn}>
          {loading ? "Loading..." : "Fetch Data"}
        </button>

        {queryResult && (
          <div style={{ overflowX: "auto", marginTop: 12 }}>
            <p>{queryResult.count} rows</p>
            <table style={{ borderCollapse: "collapse", width: "100%" }}>
              <thead>
                <tr>
                  {queryResult.columns.map((col) => (
                    <th key={col} style={th}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {queryResult.rows.map((row, i) => (
                  <tr key={i}>
                    {queryResult.columns.map((col) => (
                      <td key={col} style={td}>{String(row[col] ?? "")}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

const btn = { padding: "8px 16px", marginRight: 8, cursor: "pointer" };
const pre = { background: "#f4f4f4", padding: 12, borderRadius: 6, marginTop: 8, overflowX: "auto" };
const th = { border: "1px solid #ccc", padding: 8, background: "#f0f0f0", textAlign: "left" };
const td = { border: "1px solid #ccc", padding: 8 };
