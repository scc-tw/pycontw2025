/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Theme 5: Warm Civic Sans - Clear and cozy
        'theme': {
          'bg': '#FFFDF9',         // Warm off-white
          'surface': '#FFFFFF',
          'ink': '#151515',        // Soft black
          'muted': '#5D605F',
          'ui': '#EDE7DD',
          'accent': '#0F7B99',     // Teal accent
          'border': '#E7DFD0',
          'focus': '#0F7B99',
          'success': '#1F7A3F',
          'warning': '#9C6A00',
          'error': '#B3261E',
          'track': {
            '1': '#2E7D8C',       // Teal
            '2': '#7A5EA8',       // Purple
            '3': '#3A8F6A',       // Green
            '4': '#C9742A'        // Orange
          },
          'hover': {
            'surface': '#FFFBF3',
            'accent': '#0D6C87'
          },
          'active': {
            'surface': '#FBF4E6',
            'accent': '#0B5E74'
          }
        },
        // Keep original pycon colors as fallback
        'pycon': {
          'blue': '#1e3a5f',
          'gold': '#ffdb58',
          'light-blue': '#4a90e2',
          'dark': '#0f1419'
        }
      },
      fontFamily: {
        'sans': ['"IBM Plex Sans"', '"Noto Sans TC"', 'system-ui', 'Segoe UI', 'Roboto', 'Arial', 'sans-serif'],
        'serif': ['"IBM Plex Serif"', '"Noto Serif TC"', 'serif'],
        'mono': ['"IBM Plex Mono"', 'ui-monospace', 'monospace']
      },
      fontSize: {
        'display': ['3.125rem', { lineHeight: '1.14', fontWeight: '600' }],  // 50px
        'headline': ['1.875rem', { lineHeight: '1.28', fontWeight: '600' }], // 30px
        'title': ['1.1875rem', { lineHeight: '1.34', fontWeight: '600' }],   // 19px
        'body': ['1rem', { lineHeight: '1.58', fontWeight: '400' }],         // 16px
        'label': ['0.75rem', { lineHeight: '1.2', fontWeight: '600', letterSpacing: '0.02em' }]  // 12px
      },
      spacing: {
        'gap-xs': '4px',
        'gap-sm': '8px',
        'gap-md': '12px',
        'gap-lg': '16px',
        'gap-xl': '24px',
        'gap-xxl': '32px'
      },
      borderRadius: {
        'sm': '12px',
        'md': '14px',
        'lg': '16px',
        'full': '9999px'
      },
      boxShadow: {
        'card': '0 4px 18px rgba(0,0,0,.06)',
        'hover': '0 6px 24px rgba(0,0,0,.08)',
        'focus': '0 0 0 2px #0F7B99'
      },
      maxWidth: {
        'content': '1160px',
        'readable': '74ch'
      },
      animation: {
        'fade-in': 'fadeIn 160ms ease-in-out',
        'slide-up': 'slideUp 160ms ease-in-out'
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' }
        }
      }
    },
  },
  plugins: [],
}