/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Увімкнення темної теми через клас
  theme: {
    extend: {
      colors: {
        darkBg: '#1E293B', // Темний фон
        darkText: '#E2E8F0', // Світлий текст
        darkCard: '#334155', // Темний колір для карток
      },
    },
  },
  plugins: [],
}
