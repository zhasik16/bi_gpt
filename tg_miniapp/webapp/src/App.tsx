import React, { useState } from "react";

type Row = Record<string, any>;
type ApiResp = {
  sql?: string;
  explain?: string;
  data?: Row[];
};

const App: React.FC = () => {
  const [q, setQ] = useState<string>("");
  const [resp, setResp] = useState<ApiResp | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  async function send() {
    if (!q.trim()) return;
    setLoading(true);
    setError("");
    setResp(null);

    try {
      const r = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });

      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || JSON.stringify(data));
      setResp(data as ApiResp);
    } catch (e: any) {
      setError(e?.message ?? "Unknown error");
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
        <div style={{ marginTop: 20, textAlign: "left" }}>
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

          <h4 style={{ marginTop: 12 }}>Результаты:</h4>

          {resp.data && resp.data.length > 0 ? (
            <div style={{ overflowX: "auto" }}>
              {(() => {
                const cols = Object.keys(resp.data![0]);
                return (
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
                        {cols.map((c) => (
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
                      {resp.data!.map((row, i) => (
                        <tr key={i}>
                          {cols.map((col, j) => {
                            const v = row[col];
                            const cell = v === null || v === undefined ? "NULL" : String(v);
                            return (
                              <td
                                key={j}
                                style={{
                                  border: "1px solid #ccc",
                                  padding: 8,
                                  color: "#111",
                                  background: i % 2 === 0 ? "#fafafa" : "#f5f5f5",
                                }}
                              >
                                {cell}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                );
              })()}
            </div>
          ) : (
            <div>Нет данных</div>
          )}
        </div>
      )}
    </div>
  );
};

export default App;
