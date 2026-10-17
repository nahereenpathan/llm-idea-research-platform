/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef6ff',
          100: '#d9ebff',
          200: '#bcdbff',
          300: '#8ec2ff',
          400: '#589eff',
          500: '#2f79f6',
          600: '#1b5ceb',
          700: '#1447d8',
          800: '#173aad',
          900: '#0f266e',
          950: '#0a1744',
        },
        navy: {
          800: '#0b1329',
          900: '#070d1e',
          950: '#040711',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
