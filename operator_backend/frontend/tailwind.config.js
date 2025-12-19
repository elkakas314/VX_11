/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#0b1220",
        surface: "#0f172a",
        accent1: "#22d3ee",
        accent2: "#f97316",
        ok: "#22c55e",
        error: "#ef4444",
        muted: "#7c92b0",
        border: "#1f2f45",
        panel: "#0c141f"
      },
      boxShadow: {
        glow: "0 0 24px rgba(34,211,238,0.2)",
        card: "0 10px 30px rgba(0,0,0,0.35)"
      },
      borderRadius: {
        card: "14px"
      }
    }
  },
  plugins: []
};
