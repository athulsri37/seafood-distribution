/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ocean: {
          50: "#eef6f9",
          100: "#d4e9f0",
          500: "#1c6e8c",
          600: "#155a72",
          700: "#0f4657",
        },
      },
    },
  },
  plugins: [],
};
