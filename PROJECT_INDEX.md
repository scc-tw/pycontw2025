# Project Index - PyCon TW 2025 FFI Talk Resources

## 📋 Project Overview

**Title**: The Hidden Corners of Python FFI  
**Speaker**: scc @ CyCraft  
**Conference**: PyCon Taiwan 2025 - Day 1, Room R3  
**Level**: Advanced  
**Focus**: Python Foreign Function Interface Performance Analysis  

## 🎯 Talk Topics

1. **FFI Benchmarks**: Comparing ctypes, cffi, pybind11, and PyO3 performance
2. **Free-Threading Impact**: Why Free-Threaded Python makes FFI slower
3. **Performance Analysis**: Using perf & gdb tracing to understand bottlenecks
4. **Racing Conditions**: FFI race conditions after No-GIL
5. **Memory Leaks**: Higher risk for Arena leakage in glibc

## 🏗️ Architecture Overview

### Technology Stack
- **Frontend Framework**: Vue 3.5 (Composition API)
- **Build Tool**: Vite 6.0
- **Language**: TypeScript 5.7 (strict mode, no `any`)
- **Styling**: Tailwind CSS 3.4
- **Routing**: Vue Router 4.5 (hash mode)
- **Syntax Highlighting**: Shiki 1.24
- **Markdown**: markdown-it 14.1

### Design Patterns
- **Service Layer**: Dependency Injection with ServiceContainer
- **State Management**: Reactive state using Vue's `reactive()`
- **Component Architecture**: Single File Components (SFC)
- **Error Handling**: Centralized ErrorService with boundaries

## 📁 Directory Structure

```
pycontw2025/
├── .github/workflows/
│   └── deploy.yml                 # GitHub Actions CI/CD
├── src/
│   ├── components/                # Reusable Vue Components
│   ├── services/                  # Service Layer (DI)
│   ├── views/                     # Page Components
│   ├── composables/               # Vue Composition Functions
│   ├── types/                     # TypeScript Type Definitions
│   ├── utils/                     # Utility Functions
│   ├── router/                    # Routing Configuration
│   ├── assets/                    # Static Assets
│   └── main.ts                    # Application Entry Point
├── scripts/
│   └── generate-manifest.js       # Auto-generate file listing
├── public/
│   ├── resources/                 # Talk Resources
│   │   ├── source/               # Source code files
│   │   └── data/                 # Benchmark data
│   ├── manifest.json             # Auto-generated file index
│   └── CNAME                     # Custom domain config
├── tests/                        # Test Suite
└── dist/                         # Production Build
```

## 🧩 Component Index

### Views (Pages)

| Component | Path | Purpose |
|-----------|------|---------|
| `HomePage.vue` | `/` | Landing page with talk info and navigation |
| `SourceCode.vue` | `/source` | Source code browser with file tree |
| `BenchmarkData.vue` | `/data` | Data visualization and downloads |

### Components

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| `FolderTree.vue` | Recursive file tree navigation | Expand/collapse, file selection |
| `CodeViewer.vue` | Syntax-highlighted code display | Multi-language support, copy function |
| `DataVisualizer.vue` | Data format visualization | CSV tables, JSON, images, SVG |
| `ResourceCard.vue` | Homepage navigation cards | File counts, descriptions |
| `LoadingState.vue` | Loading indicators | Skeleton screens |
| `ErrorBoundary.vue` | Error handling wrapper | Graceful error display |

### Services

| Service | Interface | Purpose |
|---------|-----------|---------|
| `ServiceContainer` | - | Dependency injection container |
| `FileService` | `IFileService` | File operations, manifest loading, caching |
| `NavigationService` | `INavigationService` | Reactive navigation state management |
| `ConfigService` | `IConfigService` | Application configuration |
| `ErrorService` | `IErrorService` | Centralized error handling |
| `PerformanceService` | `IPerformanceService` | Performance monitoring |

### Composables

| Composable | Purpose |
|------------|---------|
| `useServices()` | Service injection hook |
| `useAccessibility()` | Accessibility utilities |

### Utilities

| Utility | Functions | Purpose |
|---------|-----------|---------|
| `fileHelpers.ts` | `getFileType()`, `getFileIcon()`, `getFileLanguage()` | File type detection and icons |

## 📊 Supported File Types

### Source Code
- **Python**: `.py`, `.pyx`, `.pyi`
- **Rust**: `.rs`
- **C/C++**: `.c`, `.h`, `.cpp`, `.cc`, `.hpp`
- **Shell**: `.sh`, `.bash`, `.zsh`
- **JavaScript/TypeScript**: `.js`, `.ts`, `.jsx`, `.tsx`
- **Configuration**: `.yaml`, `.yml`, `.toml`, `Makefile`

### Data Formats
- **Tables**: `.csv`, `.tsv`
- **JSON**: `.json`
- **Performance**: `.data`, `.perf`
- **Visualizations**: `.svg`
- **Images**: `.png`, `.jpg`, `.gif`, `.webp`
- **Documents**: `.pdf`, `.md`, `.txt`

## 🚀 Key Features

### File Management
- ✅ Nested folder navigation with reactive state
- ✅ Real-time folder expansion/collapse
- ✅ Breadcrumb navigation
- ✅ Automatic manifest generation

### Code Display
- ✅ Syntax highlighting for 15+ languages
- ✅ One-click copy to clipboard
- ✅ Line numbers and formatting
- ✅ Mobile-responsive viewer

### Data Visualization
- ✅ Interactive CSV/TSV tables
- ✅ JSON pretty-printing
- ✅ SVG inline rendering with zoom
- ✅ Image display with optimization

### Performance
- ✅ Lazy loading with Suspense
- ✅ Service worker caching
- ✅ Code splitting by route
- ✅ Optimized bundle size (~150KB)

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `vite.config.ts` | Vite build configuration |
| `tsconfig.json` | TypeScript compiler options |
| `tailwind.config.js` | Tailwind CSS customization |
| `package.json` | Dependencies and scripts |
| `.github/workflows/deploy.yml` | GitHub Actions deployment |

## 📝 Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Development server (localhost:5173) |
| `npm run build` | Production build with manifest |
| `npm run preview` | Preview production build |
| `npm run generate-manifest` | Generate file listing |
| `npm run type-check` | TypeScript validation |
| `npm run lint` | ESLint code quality |
| `npm run test` | Run test suite |

## 🌐 Deployment

- **GitHub Pages**: Automated deployment via GitHub Actions
- **Custom Domain**: pycontw2025.scc.tw (via Cloudflare CNAME)
- **Build Process**: 
  1. Generate manifest from public/resources/
  2. TypeScript compilation
  3. Vite production build
  4. Deploy to GitHub Pages

## 🎨 Theme Customization

### Color Palette
```javascript
colors: {
  'pycon': {
    'blue': '#1e3a5f',      // Primary brand color
    'gold': '#ffdb58',      // Accent color
    'light-blue': '#4a90e2', // Secondary color
    'dark': '#0f1419'       // Dark backgrounds
  }
}
```

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `README.md` | Project overview and setup |
| `PROJECT_INDEX.md` | This comprehensive index |
| `GITHUB_ACTIONS_VERIFICATION.md` | Deployment verification |
| `LICENSE` | GPL-3.0-or-later license |

## 🔗 External Links

- **GitHub Repository**: [github.com/scc-tw/pycontw2025](https://github.com/scc-tw/pycontw2025)
- **Live Site**: [pycontw2025.scc.tw](https://pycontw2025.scc.tw)
- **Talk Details**: [PyCon TW 2025 Talk #349](https://tw.pycon.org/2025/en-us/conference/talk/349)

## 📊 Project Metrics

- **Components**: 6 reusable components
- **Services**: 5 injected services
- **Views**: 3 main pages
- **File Types Supported**: 20+
- **Bundle Size**: ~150KB (gzipped: ~50KB)
- **TypeScript Coverage**: 100% (no `any` types)

---

*Last Updated: 2025*  
*Generated for PyCon Taiwan 2025 - The Hidden Corners of Python FFI*