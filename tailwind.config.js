/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Theme 4: Playful Pastel Tech - Friendly but focused
        'theme': {
          'bg': '#FBFDFF',         // Very light blue-tinted white
          'surface': '#FFFFFF',
          'ink': '#1A1F2C',        // Dark blue-gray
          'muted': '#5B6472',
          'ui': '#E6EEF6',
          'accent': '#00B8D9',     // Cyan accent
          'border': '#D9E6F2',
          'focus': '#00B8D9',
          'track': {
            '1': '#82C0FF',       // Light blue
            '2': '#B9A6FF',       // Light purple
            '3': '#7EE3C1',       // Light teal
            '4': '#FFC69E'        // Light peach
          },
          'hover': {
            'surface': '#F4F9FF',
            'accent': '#00A4C3'
          },
          'active': {
            'surface': '#EDF5FD',
            'accent': '#008FAA'
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
        'mono': ['"IBM Plex Mono"', 'ui-monospace', 'monospace']
      },
      fontSize: {
        'display': ['3.25rem', { lineHeight: '1.1', fontWeight: '600' }],    // 52px
        'headline': ['1.875rem', { lineHeight: '1.25', fontWeight: '600' }], // 30px
        'title': ['1.125rem', { lineHeight: '1.35', fontWeight: '600' }],    // 18px
        'body': ['1rem', { lineHeight: '1.55', fontWeight: '400' }],         // 16px
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
        'sm': '14px',
        'md': '16px',
        'lg': '20px',
        'full': '9999px'
      },
      boxShadow: {
        'card': '0 8px 28px rgba(10,31,44,.08)',
        'hover': '0 12px 32px rgba(10,31,44,.10)',
        'focus': '0 0 0 2px #00B8D9'
      },
      maxWidth: {
        'content': '1200px',
        'readable': '74ch'
      },
      animation: {
        'fade-in': 'fadeIn 180ms cubic-bezier(.16,1,.3,1)',
        'slide-up': 'slideUp 180ms cubic-bezier(.16,1,.3,1)',
        'bounce-gentle': 'bounceGentle 600ms cubic-bezier(.16,1,.3,1)'
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' }
        },
        bounceGentle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' }
        }
      }
    },
  },
  plugins: [],
}