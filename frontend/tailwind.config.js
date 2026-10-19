/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        editor: {
          bg: '#0c0d10',
          panel: '#14151b',
          subpanel: '#1b1d24',
          border: '#272935',
          hover: '#2d303e',
          text: '#f1f3f9',
          muted: '#8b90a0',
          accent: '#6366f1',
          accentHover: '#4f46e5',
        },
        surface: {
          base: '#0c0d10',
          raised: '#14151b',
          hover: '#1e202a',
          active: '#272935',
          border: '#272935',
        },
        border: {
          default: '#272935',
          subtle: '#1b1d24',
        },
        text: {
          primary: '#f1f3f9',
          secondary: '#9da3b4',
          muted: '#686d7e',
        },
        accent: {
          blue: '#4f46e5',
          green: '#10b981',
          amber: '#f59e0b',
          rose: '#f43f5e',
        }
      }
    },
  },
  plugins: [],
}
