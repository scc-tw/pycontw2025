import type { FileNode } from '@/types/resources'

export const buildFileTree = async (basePath: string): Promise<FileNode[]> => {
  try {
    // Try to fetch the manifest file first
    const response = await fetch('/manifest.json')
    if (response.ok) {
      const manifest = await response.json()
      return transformToFileTree(manifest.files || [], basePath)
    }
  } catch {
    console.warn('Manifest not found, using mock data')
  }
  
  // Return mock data for development
  return getMockFileTree(basePath)
}

const transformToFileTree = (
  files: string[], 
  basePath: string
): FileNode[] => {
  const root: Map<string, FileNode> = new Map()
  const tree: FileNode[] = []
  
  // Sort files to ensure directories are created before their children
  files.sort()
  
  files.forEach(filePath => {
    const parts = filePath.split('/').filter(Boolean)
    let currentPath = basePath
    let parentChildren = tree
    
    parts.forEach((part, index) => {
      currentPath = `${currentPath}/${part}`
      const isFile = index === parts.length - 1 && part.includes('.')
      
      if (!root.has(currentPath)) {
        const node: FileNode = {
          name: part,
          path: currentPath,
          type: isFile ? 'file' : 'directory',
          extension: isFile ? part.split('.').pop() : undefined,
          language: isFile ? detectLanguage(part) : undefined
        }
        
        if (!isFile) {
          node.children = []
        }
        
        root.set(currentPath, node)
        parentChildren.push(node)
      }
      
      const currentNode = root.get(currentPath)!
      if (!isFile && currentNode.children) {
        parentChildren = currentNode.children
      }
    })
  })
  
  return tree
}

export const detectLanguage = (filename: string): string => {
  const ext = filename.split('.').pop()?.toLowerCase()
  const languageMap: Record<string, string> = {
    // Programming Languages
    'py': 'python',
    'pyx': 'cython',
    'pyi': 'python',
    'rs': 'rust',
    'c': 'c',
    'h': 'c',
    'cpp': 'cpp',
    'cc': 'cpp',
    'cxx': 'cpp',
    'hpp': 'cpp',
    'hxx': 'cpp',
    'ts': 'typescript',
    'tsx': 'typescriptreact',
    'js': 'javascript',
    'jsx': 'javascriptreact',
    'vue': 'vue',
    
    // Shell & Scripts
    'sh': 'shell',
    'bash': 'shell',
    'zsh': 'shell',
    'fish': 'shell',
    
    // Build & Config
    'makefile': 'makefile',
    'mk': 'makefile',
    'toml': 'toml',
    'yaml': 'yaml',
    'yml': 'yaml',
    'json': 'json',
    'jsonc': 'json',
    'xml': 'xml',
    'ini': 'ini',
    'cfg': 'ini',
    'conf': 'conf',
    
    // Documentation
    'md': 'markdown',
    'mdx': 'markdown',
    'rst': 'restructuredtext',
    'txt': 'text',
    'pdf': 'pdf',
    
    // Data & Benchmark Files
    'csv': 'csv',
    'tsv': 'tsv',
    'data': 'binary',
    'perf': 'perfdata',
    'svg': 'svg',
    'png': 'image',
    'jpg': 'image',
    'jpeg': 'image',
    'gif': 'image',
    'webp': 'image',
    
    // Web
    'html': 'html',
    'htm': 'html',
    'css': 'css',
    'scss': 'scss',
    'sass': 'sass',
    'less': 'less'
  }
  
  // Special case for Makefile
  if (filename.toLowerCase() === 'makefile') {
    return 'makefile'
  }
  
  return languageMap[ext || ''] || 'text'
}

export const getFileIcon = (node: FileNode): string => {
  if (node.type === 'directory') {
    return '📁'
  }
  
  const iconMap: Record<string, string> = {
    // Programming Languages
    'python': '🐍',
    'cython': '🐍',
    'rust': '🦀',
    'c': '🔷',
    'cpp': '🔶',
    'javascript': '📜',
    'javascriptreact': '⚛️',
    'typescript': '📘',
    'typescriptreact': '⚛️',
    'vue': '💚',
    
    // Shell & Scripts
    'shell': '🖥️',
    
    // Build & Config
    'makefile': '🔨',
    'toml': '⚙️',
    'yaml': '⚙️',
    'json': '📋',
    'xml': '📄',
    'ini': '⚙️',
    'conf': '⚙️',
    
    // Documentation
    'markdown': '📝',
    'restructuredtext': '📝',
    'text': '📄',
    'pdf': '📕',
    
    // Data & Benchmark Files
    'csv': '📊',
    'tsv': '📊',
    'binary': '💾',
    'perfdata': '⚡',
    'svg': '🎨',
    'image': '🖼️',
    
    // Web
    'html': '🌐',
    'css': '🎨',
    'scss': '🎨',
    'sass': '🎨',
    'less': '🎨'
  }
  
  return iconMap[node.language || ''] || '📄'
}

// Mock data for development
export const getMockFileTree = (basePath: string): FileNode[] => {
  const mockStructure = {
    source: {
      // Python test suite
      tests: {
        unit: ['test_utils.py', 'test_core.py', 'test_benchmarks.py', 'conftest.py'],
        integration: ['test_api.py', 'test_workflow.py', 'test_performance.py'],
        e2e: ['test_full_flow.py', 'test_system.py'],
        fixtures: ['data.json', 'config.toml', 'test_data.csv']
      },
      // Main source code
      src: {
        core: ['main.py', 'utils.py', 'config.py', 'types.pyi'],
        benchmarks: ['cpu_bench.py', 'memory_bench.py', 'io_bench.py', 'network_bench.py'],
        analysis: ['analyzer.py', 'reporter.py', 'visualizer.py'],
        native: ['optimizer.c', 'fast_compute.cpp', 'bindings.pyx']
      },
      // Rust components
      rust: [
        'Cargo.toml', 'Cargo.lock', 'lib.rs', 'bench.rs', 
        'ffi.rs', 'bindings.h'
      ],
      // Build files
      build: ['Makefile', 'setup.py', 'pyproject.toml', 'requirements.txt'],
      // Scripts
      scripts: ['run_tests.sh', 'benchmark.sh', 'deploy.sh', 'analyze.py'],
      // Documentation
      docs: ['README.md', 'CONTRIBUTING.md', 'API.md', 'CHANGELOG.md']
    },
    data: {
      // Benchmark results
      benchmarks: {
        cpu: [
          'cpu_profile.json', 'cpu_benchmark.csv', 'cpu_report.txt',
          'cpu_flame.svg', 'cpu_timeline.png'
        ],
        memory: [
          'memory_profile.json', 'heap_dump.data', 'memory_usage.csv',
          'memory_graph.svg', 'allocation_chart.png'
        ],
        io: [
          'disk_benchmark.json', 'io_perf.data', 'throughput.csv',
          'io_heatmap.svg', 'latency_distribution.png'
        ],
        network: [
          'network_trace.json', 'packet_analysis.csv', 'bandwidth.txt',
          'network_topology.svg', 'latency_map.png'
        ]
      },
      // Performance data
      perf: [
        'perf.data', 'perf_report.txt', 'flamegraph.svg',
        'callgrind.out', 'cachegrind.out'
      ],
      // Analysis results
      analysis: {
        '2024': [
          'q1_analysis.json', 'q2_analysis.json', 'q3_analysis.json', 'q4_analysis.json',
          'yearly_summary.md', 'trends.csv'
        ],
        '2025': [
          'jan_metrics.json', 'feb_metrics.json', 'current_state.csv',
          'predictions.json', 'optimization_report.pdf'
        ]
      },
      // Visualizations
      visualizations: {
        charts: [
          'performance_over_time.svg', 'memory_usage.svg', 'cpu_utilization.svg',
          'comparison_chart.png', 'heatmap.png'
        ],
        graphs: [
          'dependency_graph.svg', 'call_graph.svg', 'network_topology.svg',
          'execution_flow.png'
        ],
        reports: ['final_report.md', 'executive_summary.pdf', 'technical_details.pdf']
      },
      // Presentation materials
      slides: [
        'pycon_tw_2025_presentation.pdf',
        'benchmark_methodology.pdf',
        'performance_optimization.pdf',
        'case_studies.pdf'
      ]
    }
  }
  
  interface MockStructure {
    [key: string]: MockStructure | string[]
  }
  
  const buildMockTree = (obj: MockStructure, currentPath: string): FileNode[] => {
    const nodes: FileNode[] = []
    
    Object.entries(obj).forEach(([key, value]) => {
      const nodePath = `${currentPath}/${key}`
      
      if (Array.isArray(value)) {
        // It's a directory with files
        const dirNode: FileNode = {
          name: key,
          path: nodePath,
          type: 'directory',
          children: value.map(fileName => ({
            name: fileName,
            path: `${nodePath}/${fileName}`,
            type: 'file',
            extension: fileName.split('.').pop(),
            language: detectLanguage(fileName)
          }))
        }
        nodes.push(dirNode)
      } else if (typeof value === 'object') {
        // It's a nested directory
        const dirNode: FileNode = {
          name: key,
          path: nodePath,
          type: 'directory',
          children: buildMockTree(value, nodePath)
        }
        nodes.push(dirNode)
      }
    })
    
    return nodes
  }
  
  if (basePath.includes('source')) {
    return buildMockTree({ ...mockStructure.source }, basePath)
  } else if (basePath.includes('data')) {
    return buildMockTree({ ...mockStructure.data }, basePath)
  }
  
  return []
}

export const formatFileSize = (bytes?: number): string => {
  if (!bytes) return ''
  
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`
}