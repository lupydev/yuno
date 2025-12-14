/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
        fontFamily: {
            rounded: ["Nunito", "system-ui", "sans-serif"],
        },
    },
  },
  plugins: [],
}

