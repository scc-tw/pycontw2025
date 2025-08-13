/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Theme 2: Editorial Cozy
        'theme': {
          'bg': '#FAF7F2',         // Oatmeal background
          'surface': '#FFFFFF',
          'ink': '#222222',        // Charcoal text
          'muted': '#6C6C6C',
          'ui': '#EDE8E1',
          'accent': '#2D6A4F',     // Sage green accent
          'border': '#E7E0D6',
          'focus': '#2D6A4F',
          'track': {
            '1': '#6B705C',      // Muted sage
            '2': '#0A9396',      // Teal
            '3': '#9A6D38',      // Clay
            '4': '#3D5A80'       // Midnight blue
          },
          'hover': {
            'surface': '#FFFBF5',
            'accent': '#285C45'
          },
          'active': {
            'surface': '#F6EFE6',
            'accent': '#234F3B'
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
        'sans': ['"IBM Plex Sans"', '"Noto Sans TC"', 'system-ui', 'sans-serif'],
        'serif': ['"IBM Plex Serif"', '"Noto Serif TC"', 'serif'],
        'mono': ['"IBM Plex Mono"', 'ui-monospace', 'monospace']
      },
      fontSize: {
        'display': ['3rem', { lineHeight: '1.15', fontWeight: '600' }],     // 48px
        'headline': ['1.75rem', { lineHeight: '1.3', fontWeight: '600' }],  // 28px
        'title': ['1.25rem', { lineHeight: '1.35', fontWeight: '600' }],    // 20px
        'body': ['1.0625rem', { lineHeight: '1.6', fontWeight: '400' }],    // 17px
        'label': ['0.75rem', { lineHeight: '1.2', fontWeight: '600', letterSpacing: '0.02em' }]  // 12px
      },
      spacing: {
        'gap-md': '16px',
        'gap-lg': '24px',
        'gap-xl': '32px'
      },
      borderRadius: {
        'sm': '14px',
        'md': '18px',
        'lg': '20px',
        'full': '9999px'
      },
      boxShadow: {
        'card': '0 6px 24px rgba(0,0,0,.06)',
        'hover': '0 8px 32px rgba(0,0,0,.08)',
        'focus': '0 0 0 2px #2D6A4F'
      },
      maxWidth: {
        'content': '1100px',
        'readable': '75ch'
      },
      animation: {
        'fade-in': 'fadeIn 180ms ease-out',
        'slide-up': 'slideUp 180ms ease-out'
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