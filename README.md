# PyCon TW 2025 Resource Assets Page

A Vue 3 + Vite + TypeScript application for hosting and presenting benchmark resources, source code, and data visualizations for PyCon Taiwan 2025 conference talk.

## 🌐 Live Demo

Visit: [https://pycontw2025.scc.tw/](https://pycontw2025.scc.tw/)

## 🚀 Key Features

### File Management
- **📁 Nested Folder Navigation**: Interactive file tree with expand/collapse functionality
- **🔄 Reactive State Management**: Real-time folder expansion and file selection
- **📍 Breadcrumb Navigation**: Clear path display with home navigation

### Code Display
- **💻 Source Code Browser**: Syntax highlighting for 15+ programming languages
- **🐍 Python Support**: Full support for .py, .pyx, .pyi files
- **🦀 Rust Support**: Complete Rust file viewing capabilities
- **🔧 C/C++ Support**: View C, C++, header files with proper highlighting
- **📜 Script Support**: Shell, Bash, Zsh script viewing

### Data Visualization
- **📊 Interactive Tables**: CSV/TSV data rendered as sortable tables
- **📈 SVG Charts**: Inline rendering with zoom controls
- **🖼️ Image Display**: Support for PNG, JPG, GIF, WebP formats
- **📄 PDF Viewer**: Embedded PDF viewing with download option
- **🔢 JSON Pretty Print**: Formatted JSON with syntax highlighting

### User Experience
- **📋 Copy to Clipboard**: One-click code copying
- **⬇️ Direct Downloads**: Download any file type
- **📱 Responsive Design**: Mobile-optimized interface
- **♿ Accessibility**: ARIA labels and keyboard navigation
- **🎨 PyCon TW Theme**: Custom branding and colors

## 🛠️ Technology Stack

- **Vue 3.5** - Composition API with TypeScript
- **TypeScript 5.7** - Strict type checking (no unnecessary `any` types)
- **Vite 6.0** - Lightning-fast HMR and build
- **Tailwind CSS 3.4** - Utility-first styling
- **Vue Router 4.5** - Hash mode for GitHub Pages
- **Shiki 1.24** - Beautiful syntax highlighting
- **Markdown-it 14.1** - Markdown rendering
- **VueUse 11.3** - Composition utilities

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/scc-tw/pycontw2025.git
cd pycontw2025
npm install

# Add your files
cp -r your-source-files/* public/resources/source/
cp -r your-data-files/* public/resources/data/

# Start development
npm run dev

# Build and deploy
npm run build
```

Open [http://localhost:5173](http://localhost:5173) to see your files!

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
├── .github/
│   └── workflows/
│       └── deploy.yml           # GitHub Actions deployment
├── src/
│   ├── components/              # Reusable Vue components
│   │   ├── CodeViewer.vue       # Syntax-highlighted code display
│   │   ├── DataVisualizer.vue   # Multi-format data visualization
│   │   ├── FolderTree.vue       # Recursive file tree navigation
│   │   ├── LoadingState.vue     # Loading indicators
│   │   ├── ResourceCard.vue     # Homepage feature cards
│   │   └── ErrorBoundary.vue    # Error handling wrapper
│   ├── services/                # Service layer (DI pattern)
│   │   ├── ServiceContainer.ts  # Dependency injection container
│   │   ├── FileService.ts       # File operations & caching
│   │   ├── NavigationService.ts # Reactive navigation state
│   │   ├── ConfigService.ts     # App configuration
│   │   ├── ErrorService.ts      # Error handling
│   │   └── PerformanceService.ts # Performance monitoring
│   ├── views/                   # Page components
│   │   ├── HomePage.vue         # Landing page
│   │   ├── SourceCode.vue       # Source code browser
│   │   └── BenchmarkData.vue    # Data visualization page
│   ├── composables/             # Vue composition functions
│   │   ├── useServices.ts       # Service injection hook
│   │   └── useAccessibility.ts  # Accessibility utilities
│   ├── types/                   # TypeScript definitions
│   │   ├── index.ts             # Main type exports
│   │   └── resources.ts         # Resource type definitions
│   ├── utils/                   # Utility functions
│   │   └── fileHelpers.ts       # File type detection & icons
│   ├── router/                  # Vue Router configuration
│   │   └── index.ts             # Route definitions
│   └── main.ts                  # Application entry point
├── scripts/
│   └── generate-manifest.js     # Auto-generate file manifest
├── public/
│   ├── resources/               # Your actual files (add here!)
│   │   ├── source/              # Source code files
│   │   │   └── benchmarks/      # Example structure
│   │   └── data/                # Benchmark data files
│   │       └── results/         # Example structure
│   ├── manifest.json            # Auto-generated file listing
│   └── CNAME                    # Custom domain config
├── tests/                       # Test files
│   ├── services/                # Service tests
│   └── setup.ts                 # Test configuration
└── dist/                        # Production build output
```

## 📝 Adding Your Resources

1. Place your source code files in `/public/resources/source/`
2. Place your data files in `/public/resources/data/`
3. Run `npm run build` - the manifest.json will be auto-generated

**Note**: The `manifest.json` is automatically generated from your files - no manual editing needed!

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
Proxy: DNS only (gray cloud)  # Important for GitHub Pages
TTL: Auto
```

### SSL/TLS Settings in Cloudflare

1. Go to SSL/TLS → Overview
2. Set encryption mode to "Full"
3. Enable "Always Use HTTPS"

## 🚀 Deployment

### Automatic Deployment via GitHub Actions

This project automatically deploys to GitHub Pages when you push to the `main` branch.

#### Setup GitHub Pages:

1. Go to your repository Settings → Pages
2. Under **Source**, select **GitHub Actions**
3. The site will deploy automatically on every push to `main`

#### How it works:

1. **Push to main** → GitHub Actions triggers
2. **Build Process**:
   - Installs dependencies
   - Scans `/public/resources/` directory
   - Auto-generates `manifest.json` with all files
   - Builds Vue application
   - Copies all public files to dist
3. **Deploy** → Publishes to GitHub Pages with custom domain

#### Manual Deployment:

1. Go to **Actions** tab in your repository
2. Select **Deploy to GitHub Pages** workflow
3. Click **Run workflow** → Select `main` branch → Run

#### Adding New Files:

```bash
# Add files to public/resources/
public/resources/
├── data/        # CSV, JSON, SVG files
└── source/      # Python, C++, Rust code

# Commit and push - auto deploys!
git add .
git commit -m "Add new benchmark data"
git push origin main
```

## 📊 Supported File Types

### Source Code
- Python (.py, .pyx, .pyi)
- Rust (.rs)
- C/C++ (.c, .h, .cpp, .cc, .hpp)
- Shell (.sh, .bash, .zsh)
- TypeScript/JavaScript (.ts, .js, .tsx, .jsx)
- YAML (.yaml, .yml)
- TOML (.toml)
- Makefile

### Data Formats
- CSV/TSV - Interactive tables
- JSON - Pretty-printed with syntax highlighting
- Performance data (.data, .perf) - Download links
- SVG - Inline rendering with zoom
- Images - PNG, JPG, GIF, WebP
- PDF - View/download options
- Markdown - Basic HTML rendering

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

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with hot reload at localhost:5173 |
| `npm run build` | Auto-generate manifest + production build |
| `npm run preview` | Preview production build locally |
| `npm run generate-manifest` | Scan public/resources/ and create manifest.json |
| `npm run type-check` | Run TypeScript type checking |
| `npm run lint` | Run ESLint and auto-fix issues |
| `npm run test` | Run unit tests with Vitest |
| `npm run test:ui` | Run tests with interactive UI |
| `npm run test:coverage` | Generate test coverage report |

## 🏗️ Architecture

### Service Layer Pattern
The application uses a **Dependency Injection (DI) pattern** with a service layer for clean separation of concerns:

- **ServiceContainer**: Central DI container managing all service instances
- **FileService**: Handles file operations, manifest loading, and caching
- **NavigationService**: Manages reactive navigation state and folder expansion
- **ConfigService**: Application configuration management
- **ErrorService**: Centralized error handling and reporting
- **PerformanceService**: Performance monitoring and metrics

### State Management
- **Reactive State**: Uses Vue 3's `reactive()` for real-time UI updates
- **Navigation State**: Centralized in NavigationService for consistent behavior
- **File Tree State**: Manages expanded folders and selected files

### TypeScript Best Practices
- **Strict Type Checking**: No unnecessary `any` types
- **Interface-First Design**: All services implement interfaces
- **Generic Types**: Used for flexible, type-safe code
- **Type Guards**: Proper unknown type handling

## 🧪 Testing

```bash
# Run unit tests
npm run test

# Run tests with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

The project includes unit tests for critical services and components using Vitest.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🐛 Troubleshooting

### Common Issues

**Folder expansion not working**
- Ensure NavigationService is properly initialized
- Check browser console for navigation errors
- Verify manifest.json is properly generated

**Files not displaying**
- Run `npm run generate-manifest` to regenerate file listing
- Check that files are in `/public/resources/` directory
- Verify file permissions are correct

**GitHub Pages 404 errors**
- Ensure hash routing is used (not history mode)
- Check CNAME file is present in public directory
- Verify GitHub Pages is enabled in repository settings

**Build failures**
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version (requires v18+)
- Ensure all TypeScript errors are resolved

## 📄 License

GPL-3.0-or-later. See `LICENSE` for details.

## 🙏 Acknowledgments

- PyCon Taiwan Community
- Vue.js Team
- Vite Team

## 📧 Contact

- PyCon TW: [https://tw.pycon.org](https://tw.pycon.org)
- GitHub: [https://github.com/scc-tw/pycontw2025](https://github.com/scc-tw/pycontw2025)

---

Built with ❤️ for PyCon Taiwan 2025