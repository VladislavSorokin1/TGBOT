// App.jsx
import { useEffect, useState } from "react";
import { Outlet, Link, useLocation } from "react-router-dom";
import WebApp from "@twa-dev/sdk";
import axios from "axios";

const API = "https://my-ola-api.onrender.com";

export default function App() {
  const [status, setStatus] = useState("loading…");
  const [user, setUser] = useState(null);
  const [initData, setInitData] = useState("");
  const loc = useLocation();

  // App.jsx

useEffect(() => {
  const webApp = WebApp;
  webApp.ready();
  webApp.expand();

  // Небольшая задержка, чтобы дать SDK Telegram время на полную инициализацию.
  // Это должно решить проблему "гонки состояний".
  setTimeout(() => {
    const initData = webApp.initData;

    // Проверяем, получили ли мы вообще initData
    if (!initData) {
      setStatus("auth failed (initData is empty after 100ms)");
      return;
    }

    // Если данные получены, отправляем запрос на наш бэкенд для верификации
    setStatus("authorizing...");
    axios.get(`${API}/api/me`, { headers: { "X-Telegram-InitData": initData } })
      .then(r => {
        setUser(r.data.user);
        setStatus("ok");
      })
      .catch((err) => {
        // Выводим более подробную информацию об ошибке
        const errorDetail = err.response?.data?.detail || err.message;
        setStatus(`auth failed (API error: ${errorDetail})`);
      });

  }, 100); // 100 миллисекунд задержки

}, []); // Пустой массив зависимостей, чтобы этот код выполнился один раз

  return (
    <div style={{fontFamily:"system-ui", minHeight:"100vh", background:"#0f1115", color:"#e6e6e6"}}>
      <header style={{position:"sticky", top:0, zIndex:10, backdropFilter:"blur(8px)", background:"rgba(15,17,21,0.6)", borderBottom:"1px solid #222"}}>
        <nav style={{display:"flex", gap:12, alignItems:"center", padding:"10px 12px"}}>
          <strong style={{marginRight:"auto"}}>NU OLA</strong>
          <NavLink to="/" current={loc.pathname==="/"}>🏠 Головна</NavLink>
          <NavLink to="/profile" current={loc.pathname==="/profile"}>👤 Профіль</NavLink>
          <NavLink to="/schedule" current={loc.pathname==="/schedule"}>📅 Розклад</NavLink>
        </nav>
      </header>

      <main style={{padding:"14px"}}>
        <small style={{opacity:0.7}}>Status: {status}</small>
        {/* передаём initData, чтобы страницы могли стучаться в API */}
        <Outlet context={{ API, user, status, initData }} />
      </main>
    </div>
  );
}

function NavLink({to, current, children}) {
  return (
    <Link to={to} style={{
      padding:"8px 10px",
      borderRadius:10,
      textDecoration:"none",
      color:"#e6e6e6",
      background: current ? "linear-gradient(90deg,#5b8cff22,#5b8cff11)" : "transparent",
      border: current ? "1px solid #2a3b66" : "1px solid transparent"
    }}>{children}</Link>
  );
}
