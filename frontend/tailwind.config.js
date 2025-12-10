/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'editor-bg': '#1e1e2e',
        'editor-surface': '#313244',
        'editor-border': '#45475a',
        'block-source': '#a6e3a1',
        'block-sink': '#f38ba8',
        'block-continuous': '#89b4fa',
        'block-discrete': '#fab387',
        'block-math': '#cba6f7',
        'block-routing': '#f9e2af',
      },
    },
  },
  plugins: [],
}
