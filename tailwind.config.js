/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Theme 1: Info-First Neutral
        'theme': {
          'bg': '#F8F7F5',
          'surface': '#FFFFFF',
          'ink': '#1B1B1B',
          'muted': '#6B6B6B',
          'ui': '#EAE8E3',
          'accent': '#006CFF',
          'success': '#1A7F37',
          'warning': '#B06A00',
          'error': '#B3261E',
          'border': '#E6E2DA',
          'focus': '#1B1B1B',
          'track': {
            '1': '#0E7490',
            '2': '#6D28D9',
            '3': '#059669',
            '4': '#EA580C'
          },
          'hover': {
            'surface': '#FDFDFC',
            'accent': '#0056CC'
          },
          'active': {
            'surface': '#F7F6F2',
            'accent': '#0047AA'
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
        'display': ['3.5rem', { lineHeight: '1.15', fontWeight: '600' }],  // 56px
        'headline': ['2rem', { lineHeight: '1.25', fontWeight: '600' }],    // 32px
        'title': ['1.25rem', { lineHeight: '1.3', fontWeight: '600' }],     // 20px
        'body': ['1rem', { lineHeight: '1.55', fontWeight: '400' }],        // 16px
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
        'md': '16px',
        'lg': '18px',
        'full': '9999px'
      },
      boxShadow: {
        'card': '0 2px 8px rgba(0,0,0,.08)',
        'hover': '0 4px 12px rgba(0,0,0,.12)',
        'focus': '0 0 0 2px #1B1B1B'
      },
      maxWidth: {
        'content': '1200px',
        'readable': '75ch'
      },
      animation: {
        'fade-in': 'fadeIn 160ms cubic-bezier(.2,.7,.2,1)',
        'slide-up': 'slideUp 220ms cubic-bezier(.2,.7,.2,1)'
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