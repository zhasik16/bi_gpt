import { useState } from "react";

export default function App() {
  const [q, setQ] = useState("");
  const [resp, setResp] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function send() {
    if (!q.trim()) return;
    setLoading(true);
    setError("");
    setResp(null);

    try {
      const r = await fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });

      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || JSON.stringify(data));
      setResp(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ fontFamily: "Arial, sans-serif", padding: 24 }}>
      <h2>BI-GPT Миниаппа</h2>

      <div style={{ marginBottom: 16, display: "flex", gap: 8 }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Например: показать студентов 20 лет"
          style={{
            flex: 1,
            padding: 10,
            borderRadius: 6,
            border: "1px solid #ccc",
            fontSize: 16,
          }}
        />
        <button
          onClick={send}
          disabled={loading}
          style={{
            padding: "10px 16px",
            borderRadius: 6,
            backgroundColor: "#4f46e5",
            color: "white",
            border: "none",
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Запрос..." : "Отправить"}
        </button>
      </div>

      {error && <div style={{ color: "red", marginBottom: 16 }}>{error}</div>}

      {resp && (
        <div style={{ marginTop: 20 }}>
          <h4>SQL-запрос:</h4>
          <pre style={{ background: "#1e1e1e", color: "#dcdcdc", padding: 10, borderRadius: 6 }}>
            {resp.sql}
          </pre>

          {resp.explain && (
            <>
              <h4>Пояснение:</h4>
              <div style={{ background: "#f0f0f0", padding: 10, borderRadius: 6 }}>{resp.explain}</div>
            </>
          )}

          <h4>Результаты:</h4>
          {resp.data && resp.data.length > 0 ? (
            <div style={{ overflowX: "auto" }}>
              <table
                style={{
                  borderCollapse: "collapse",
                  width: "100%",
                  marginTop: 8,
                  minWidth: 600,
                }}
              >
                <thead>
                  <tr>
                    {Object.keys(resp.data[0]).map((c) => (
                      <th
                        key={c}
                        style={{
                          border: "1px solid #ccc",
                          padding: 8,
                          background: "#333",
                          color: "#fff",
                          textAlign: "left",
                        }}
                      >
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {resp.data.map((row, i) => (
                    <tr key={i}>
                      {Object.values(row).map((v, j) => (
                        <td
                          key={j}
                          style={{
                            border: "1px solid #ccc",
                            padding: 8,
                            color: "#111",
                            background: i % 2 === 0 ? "#fafafa" : "#f5f5f5",
                          }}
                        >
                          {v !== null ? v.toString() : "NULL"}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div>Нет данных</div>
          )}
        </div>
      )}
    </div>
  );
}
