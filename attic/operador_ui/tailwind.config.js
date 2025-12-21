/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: "#6366f1",
                secondary: "#a855f7",
                critical: "#ef4444",
                warning: "#f59e0b",
                ok: "#10b981",
            },
        },
    },
    plugins: [],
    darkMode: "class",
}
