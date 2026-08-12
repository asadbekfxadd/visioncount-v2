import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#080B12",
        bgsoft: "#0A0E17",
        card: "#111827",
        cardalt: "#151E2E",
        border: "#1F2937",
        accent: "#5B6EF5",
        green: "#22C55E",
        red: "#EF4444",
        amber: "#F59E0B",
        textmuted: "#9CA3AF",
        textfaint: "#6B7280",
      },
      borderRadius: { xl: "14px" },
    },
  },
  plugins: [],
};

export default config;
