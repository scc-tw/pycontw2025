/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'pycon': {
          'blue': '#1e3a5f',
          'gold': '#ffdb58',
          'light-blue': '#4a90e2',
          'dark': '#0f1419'
        }
      }
    },
  },
  plugins: [],
}