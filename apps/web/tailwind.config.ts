import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172026",
        moss: "#47624f",
        coral: "#d96c59",
        steel: "#5d7480",
        paper: "#f7f7f2"
      }
    }
  },
  plugins: []
};

export default config;

