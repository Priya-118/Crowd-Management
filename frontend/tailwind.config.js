/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          800: "#132147",
          900: "#0b142c",
          950: "#060a17",
        },
        brand: {
          teal: "#0d9488",
          emerald: "#10b981",
          cyan: "#06b6d4",
          blue: "#2563eb",
        }
      }
    },
  },
  plugins: [],
}
