// web/src/pages/Profile.jsx

import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import axios from "axios";

// Начальное состояние формы, чтобы избежать ошибок
const initialFormState = {
  name: "",
  surname: "",
  phone: "",
  email: "",
  department: "",
  group: "", // В React-коде используем 'group', axios позаботится о правильном имени для API
  course: "",
  status: "",
  lang: "ua",
};

export default function Profile() {
  const { API, status, initData } = useOutletContext();

  // --- СОСТОЯНИЯ КОМПОНЕНТА ---
  const [profile, setProfile] = useState(null); // для исходных данных с сервера
  const [form, setForm] = useState(initialFormState); // для данных в полях ввода
  const [saving, setSaving] = useState(false); // для состояния загрузки при сохранении
  const [msg, setMsg] = useState(""); // для сообщений об успехе/ошибке
  const [err, setErr] = useState(""); // для ошибок при загрузке

  // --- ЗАГРУЗКА ДАННЫХ С СЕРВЕРА ---
  useEffect(() => {
    if (status !== "ok") return; // не авторизованы — не ходим в API

    axios.get(`${API}/api/profile`, {
      headers: { "X-Telegram-InitData": initData }
    })
    .then(r => {
      setProfile(r.data);
      // Важно: Заполняем форму данными, полученными с сервера
      setForm(r.data);
    })
    .catch(e => setErr(e?.response?.statusText || "error"));
  }, [status, API, initData]);


  // --- ОБРАБОТЧИКИ СОБЫТИЙ ---

  // Обновляет поле в состоянии формы при вводе текста
  const setField = (fieldName, value) => {
    setForm(prevForm => ({
      ...prevForm,
      [fieldName]: value
    }));
  };

  // Функция сохранения данных
  const save = async () => {
    setSaving(true);
    setMsg("");
    try {
      // Отправляем POST-запрос с текущими данными из формы
      await axios.post(`${API}/api/profile`, form, {
        headers: { "X-Telegram-InitData": initData }
      });
      setMsg("✅ Данные успешно сохранены!");
    } catch (error) {
      setMsg('🚫 Ошибка сохранения: ${error?.response?.data?.detail || "проверьте сервер"}');
    } finally {
      setSaving(false);
    }
  };

  // --- РЕНДЕРИНГ КОМПОНЕНТА ---

  if (status !== "ok") return <p style={{opacity:.7}}>Відкрийте через Telegram, щоб редагувати профіль</p>;
  if (!profile) return <p>Завантаження… {err && `(${err})`}</p>;

  // Теперь вместо <pre> мы рендерим полноценную форму
  return (
    <div>
      <h2>Профіль</h2>

      <Grid>
        <Input label="Імʼя"       value={form.name || ''}       onChange={e=>setField("name", e.target.value)} />
        <Input label="Прізвище"   value={form.surname || ''}    onChange={e=>setField("surname", e.target.value)} />
        <Input label="Телефон"    value={form.phone || ''}      onChange={e=>setField("phone", e.target.value)} />
        <Input label="Email"      value={form.email || ''}      onChange={e=>setField("email", e.target.value)} />
        <Input label="Факультет"  value={form.department || ''} onChange={e=>setField("department", e.target.value)} />
        <Input label="Група"      value={form.group || ''}      onChange={e=>setField("group", e.target.value)} />
        <Input label="Курс"       value={form.course || ''}     onChange={e=>setField("course", e.target.value)} />
        <Input label="Статус"     value={form.status || ''}     onChange={e=>setField("status", e.target.value)} />
        <Input label="Мова (ua/en)" value={form.lang || ''}     onChange={e=>setField("lang", e.target.value)} />
      </Grid>

      <button onClick={save} disabled={saving}
        style={{marginTop:12, padding:"10px 14px", borderRadius:10, border:"1px solid #2a3b66", background:"#1b2130", color:"#e6e6e6", cursor:"pointer"}}>
        {saving ? "Збереження…" : "Зберегти"}
      </button>

      {/* Отображаем сообщение о результате сохранения */}
      {msg && <p style={{marginTop:8, opacity:.8}}>{msg}</p>}
    </div>
  );
}

// Вспомогательные компоненты для верстки (остаются без изменений)
function Grid({children}) {
  return <div style={{
    display:"grid", gridTemplateColumns:"1fr 1fr", gap:12,
    background:"#12161f", border:"1px solid #232b40", padding:12, borderRadius:12
  }}>{children}</div>;
}
function Input({label, ...props}) {
  return (
    <label style={{display:"grid", gap:6}}>
      <span style={{opacity:.8}}>{label}</span>
      <input {...props} style={{padding:"10px", borderRadius:10, border:"1px solid #2a3b66", background:"#0f1115", color:"#e6e6e6"}}/>
    </label>
  );
}