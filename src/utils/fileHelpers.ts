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
    'py': 'python',
    'ts': 'typescript',
    'js': 'javascript',
    'json': 'json',
    'yaml': 'yaml',
    'yml': 'yaml',
    'md': 'markdown',
    'sh': 'shell',
    'bash': 'shell',
    'svg': 'svg',
    'csv': 'csv',
    'txt': 'text',
    'html': 'html',
    'css': 'css',
    'scss': 'scss',
    'vue': 'vue',
    'tsx': 'typescriptreact',
    'jsx': 'javascriptreact'
  }
  return languageMap[ext || ''] || 'text'
}

export const getFileIcon = (node: FileNode): string => {
  if (node.type === 'directory') {
    return '📁'
  }
  
  const iconMap: Record<string, string> = {
    'python': '🐍',
    'javascript': '📜',
    'typescript': '📘',
    'json': '📋',
    'yaml': '⚙️',
    'markdown': '📝',
    'shell': '🖥️',
    'svg': '🎨',
    'csv': '📊',
    'html': '🌐',
    'css': '🎨',
    'vue': '💚'
  }
  
  return iconMap[node.language || ''] || '📄'
}

// Mock data for development
export const getMockFileTree = (basePath: string): FileNode[] => {
  const mockStructure = {
    source: {
      benchmarks: {
        cpu: ['test_performance.py', 'config.yaml', 'README.md'],
        memory: ['memory_test.py', 'memory_profile.json'],
        io: ['disk_benchmark.py', 'network_test.py']
      },
      tests: {
        unit: ['test_utils.py', 'test_core.py'],
        integration: ['test_api.py', 'test_workflow.py'],
        e2e: ['test_full_flow.py']
      },
      scripts: ['setup.sh', 'run_benchmarks.py', 'analyze_results.py']
    },
    data: {
      results: {
        '2024': {
          'q1': ['benchmark_jan.json', 'benchmark_feb.json', 'benchmark_mar.json'],
          'q2': ['benchmark_apr.json', 'benchmark_may.json', 'benchmark_jun.json']
        },
        '2025': {
          'january': ['performance_metrics.csv', 'memory_usage.json', 'summary.md']
        }
      },
      visualizations: {
        charts: ['performance_chart.svg', 'memory_timeline.svg', 'comparison.svg'],
        graphs: ['network_graph.svg', 'dependency_graph.svg'],
        reports: ['final_report.md', 'executive_summary.pdf']
      },
      slides: ['pycon_tw_2025_presentation.pdf', 'benchmark_analysis.pdf']
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