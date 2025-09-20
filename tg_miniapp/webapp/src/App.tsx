import { useState } from "react";
import "./App.css";

export default function App() {
  const [q, setQ] = useState("");
  const [resp, setResp] = useState<any>(null);
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
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-container">
      <header>
        <h1>📊 BI-GPT Мини-App</h1>
        <p className="subtitle">Задай вопрос на русском — получи SQL и данные</p>
      </header>

      <div className="input-container">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Например: показать студентов 20 лет"
          className="input-field"
        />
        <button onClick={send} disabled={loading} className="send-btn">
          {loading ? "⏳ Запрос..." : "🚀 Отправить"}
        </button>
      </div>

      {error && <div className="error-box">❌ {error}</div>}

      {resp && (
        <div className="result-box">
          <h3>💡 SQL-запрос:</h3>
          <pre className="sql-box">{resp.sql}</pre>

          {resp.explain && (
            <>
              <h3>📖 Пояснение:</h3>
              <div className="explain-box">{resp.explain}</div>
            </>
          )}

          <h3>📋 Результаты:</h3>
          {resp.data && resp.data.length > 0 ? (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    {Object.keys(resp.data[0]).map((c) => (
                      <th key={c}>{c}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {resp.data.map((row: any, i: number) => (
                    <tr key={i}>
                      {Object.values(row).map((v, j) => (
                        <td key={j}>{v !== null ? v.toString() : "NULL"}</td>
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

      <footer>
        <p>🔗 Наши Telegram-боты:</p>
        <div className="social-links">
          <a
            href="https://t.me/wealthera_bot"
            target="_blank"
            rel="noopener noreferrer"
            className="social-link"
          >
            <img src="https://cdn-icons-png.flaticon.com/512/2111/2111646.png" alt="Telegram" />
            Wealthera Bot
          </a>
          <a
            href="https://t.me/bmaibot_bot"
            target="_blank"
            rel="noopener noreferrer"
            className="social-link"
          >
            <img src="https://cdn-icons-png.flaticon.com/512/2111/2111646.png" alt="Telegram" />
            Bmai Bot
          </a>
        </div>
      </footer>
    </div>
  );
}
