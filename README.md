# PyCon TW 2025 Resource Assets Page

A Vue 3 + Vite + TypeScript application for hosting and presenting benchmark resources, source code, and data visualizations for PyCon Taiwan 2025 talk.

## 🌐 Live Demo

Visit: [https://pycontw2025.scc.tw/](https://pycontw2025.scc.tw/)

## 🚀 Features

- **📁 Nested Folder Navigation**: Full support for nested directory structures
- **💻 Source Code Browser**: View Python scripts, YAML configs, and more with syntax highlighting
- **📊 Data Visualization**: Display CSV tables, JSON data, SVG charts, and images
- **⬇️ Direct Downloads**: Download any file directly from the browser
- **📋 Copy to Clipboard**: Quick copy functionality for code and data
- **🔍 Zoom Controls**: For SVG visualizations
- **📱 Responsive Design**: Mobile-friendly interface
- **🎨 PyCon TW Branding**: Custom theme colors

## 🛠️ Technology Stack

- **Vue 3.5** - Progressive JavaScript Framework
- **TypeScript 5.5** - Type-safe development
- **Vite 5.4** - Fast build tool
- **Tailwind CSS 3.4** - Utility-first CSS framework
- **Vue Router 4.4** - SPA routing
- **Shiki** - Syntax highlighting
- **Markdown-it** - Markdown rendering

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/scc-tw/pycontw2025.git
cd pycontw2025

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
pycontw2025/
├── src/
│   ├── components/       # Vue components
│   │   ├── FolderTree.vue       # Recursive folder navigation
│   │   ├── CodeViewer.vue       # Source code display
│   │   ├── DataVisualizer.vue   # Data visualization
│   │   └── ResourceCard.vue     # Homepage cards
│   ├── views/            # Page components
│   ├── types/            # TypeScript definitions
│   ├── composables/      # Vue composables
│   └── utils/            # Utility functions
├── public/
│   ├── resources/        # Your actual files
│   │   ├── source/       # Source code files
│   │   └── data/         # Benchmark data
│   ├── manifest.json     # File listing
│   └── CNAME            # Custom domain
└── dist/                # Production build
```

## 📝 Adding Your Resources

1. Place your source code files in `/public/resources/source/`
2. Place your data files in `/public/resources/data/`
3. Update `/public/manifest.json` with your file paths:

```json
{
  "version": "1.0.0",
  "files": [
    "resources/source/benchmarks/cpu/test.py",
    "resources/data/results/2025/metrics.csv"
  ]
}
```

## 🌐 Custom Domain Setup

### GitHub Pages Configuration

1. Push your code to GitHub
2. Go to Settings → Pages
3. Set source to "GitHub Actions"
4. The workflow will automatically deploy on push to main

### Cloudflare DNS Configuration

Add these DNS records in Cloudflare:

```
Type: CNAME
Name: pycontw2025
Target: scc-tw.github.io
Proxy: ON (orange cloud)
```

### SSL/TLS Settings in Cloudflare

1. Go to SSL/TLS → Overview
2. Set encryption mode to "Full"
3. Enable "Always Use HTTPS"

## 🚀 Deployment

The project includes GitHub Actions workflow for automatic deployment:

```yaml
# .github/workflows/deploy.yml
- Builds on push to main branch
- Deploys to GitHub Pages
- Supports custom domain via CNAME file
```

## 📊 Supported File Types

### Source Code
- Python (.py)
- YAML (.yaml, .yml)
- JSON (.json)
- Shell (.sh, .bash)
- Markdown (.md)
- TypeScript/JavaScript (.ts, .js)

### Data Formats
- CSV - Rendered as tables
- JSON - Formatted display
- SVG - Vector graphics with zoom
- Images - PNG, JPG, GIF
- Markdown - Rendered HTML

## 🎨 Customization

### Theme Colors

Edit `tailwind.config.js`:

```javascript
colors: {
  'pycon': {
    'blue': '#1e3a5f',
    'gold': '#ffdb58',
    'light-blue': '#4a90e2',
    'dark': '#0f1419'
  }
}
```

### File Icons

Customize in `/src/utils/fileHelpers.ts`:

```typescript
const iconMap: Record<string, string> = {
  'python': '🐍',
  'javascript': '📜',
  // Add more...
}
```

## 📝 Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run type-check` - Run TypeScript checks
- `npm run lint` - Run ESLint

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - Feel free to use this for your presentations!

## 🙏 Acknowledgments

- PyCon Taiwan Community
- Vue.js Team
- Vite Team

## 📧 Contact

- PyCon TW: [https://tw.pycon.org](https://tw.pycon.org)
- GitHub: [https://github.com/scc-tw/pycontw2025](https://github.com/scc-tw/pycontw2025)

---

Built with ❤️ for PyCon Taiwan 2025