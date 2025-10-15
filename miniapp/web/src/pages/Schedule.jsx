import React, { useEffect, useState } from "react";
import WebApp from "@twa-dev/sdk";

const API = "https://big-bats-raise.loca.lt"

export default function Schedule() {
  const [schedule, setSchedule] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/schedule`)
      .then((r) => r.json())
      .then((data) => {
        setSchedule(data.data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <p>Завантаження...</p>;

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">📅 Розклад</h1>
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-gray-100">
            <th className="border p-2">День</th>
            <th className="border p-2">Предмет</th>
            <th className="border p-2">Викладач</th>
            <th className="border p-2">Час</th>
            <th className="border p-2">Аудиторія</th>
          </tr>
        </thead>
        <tbody>
          {schedule.map((s) => (
            <tr key={s.id}>
              <td className="border p-2">{s.day}</td>
              <td className="border p-2">{s.subject}</td>
              <td className="border p-2">{s.teacher}</td>
              <td className="border p-2">{s.time}</td>
              <td className="border p-2">{s.room}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
