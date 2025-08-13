/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Theme 3: Minimal Monochrome - Ultra-clear design
        'theme': {
          'bg': '#FFFFFF',         // Pure white background
          'surface': '#FFFFFF',
          'ink': '#111111',        // Near-black text
          'muted': '#555555',
          'ui': '#E9E9E9',
          'accent': '#005AC2',     // Deep blue accent
          'border': '#E9E9E9',
          'focus': '#005AC2',
          'track': {
            '1': '#0F766E',       // Teal
            '2': '#7C3AED',       // Purple
            '3': '#2563EB',       // Blue
            '4': '#B45309'        // Brown
          },
          'hover': {
            'surface': '#FAFAFA',
            'accent': '#004CA3'
          },
          'active': {
            'surface': '#F5F5F5',
            'accent': '#003F87'
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
        'display': ['2.75rem', { lineHeight: '1.2', fontWeight: '600' }],    // 44px
        'headline': ['1.75rem', { lineHeight: '1.3', fontWeight: '600' }],   // 28px
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
        'sm': '10px',
        'md': '12px',
        'lg': '14px',
        'full': '9999px'
      },
      boxShadow: {
        'card': 'none',  // No shadows for minimal design
        'hover': 'none',
        'focus': '0 0 0 2px #005AC2'
      },
      maxWidth: {
        'content': '1160px',
        'readable': '72ch'
      },
      animation: {
        'fade-in': 'fadeIn 120ms linear',
        'slide-up': 'slideUp 120ms linear'
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