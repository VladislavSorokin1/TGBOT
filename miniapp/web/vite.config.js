import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,

    // Добавляем этот массив, чтобы разрешить доступ с нашего туннеля
    allowedHosts: [
      'myoladean.serveo.net' // <-- Вставьте сюда имя, которое вы выбрали
    ],

    // Прокси для API-запросов (оставляем как есть)
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})