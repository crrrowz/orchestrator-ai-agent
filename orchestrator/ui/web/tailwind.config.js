/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        base: '#080b10',
        surface: '#0f141c',
        card: '#151b26',
        cardHover: '#1c2433',
        subtle: '#232c3d',
        activeBorder: '#3a4760',
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Readex Pro', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      }
    },
  },
  plugins: [],
}
