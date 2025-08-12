import type { FileNode } from '@/types/resources'
import { getMockFileTree } from '@/utils/fileHelpers'

/**
 * Service for managing file operations and GitHub content
 * Follows Single Responsibility Principle - handles only file-related operations
 */
export interface IFileService {
  fetchFileTree(basePath: string): Promise<FileNode[]>
  fetchFileContent(path: string): Promise<string>
  getDownloadUrl(path: string): string
  getRawGitHubUrl(path: string): string
}

export class FileService implements IFileService {
  private readonly baseUrl: string
  private readonly githubRepo: string
  private readonly githubBranch: string
  private cache: Map<string, { data: unknown; timestamp: number }>

  constructor(
    baseUrl: string = '/',
    githubRepo: string = 'scc-tw/pycontw2025',
    githubBranch: string = 'gh-pages'
  ) {
    this.baseUrl = baseUrl
    this.githubRepo = githubRepo
    this.githubBranch = githubBranch
    this.cache = new Map()
  }

  /**
   * Fetches file tree from manifest or generates mock data
   * Implements caching to reduce network requests
   */
  async fetchFileTree(basePath: string): Promise<FileNode[]> {
    const cacheKey = `tree_${basePath}`
    const cached = this.getFromCache<FileNode[]>(cacheKey)
    
    if (cached) {
      return cached
    }

    try {
      const response = await fetch(`${this.baseUrl}manifest.json`)
      if (response.ok) {
        const manifest = await response.json()
        // Extract the category from basePath (e.g., 'resources/source' -> 'source')
        const category = basePath.replace(/^.*resources\//, '').replace(/\/$/, '')
        
        // Filter files based on the requested category
        const filteredFiles = (manifest.files || []).filter((file: string) => {
          return file.startsWith(category + '/')
        })
        
        // Build tree with corrected paths
        const tree = this.transformToFileTree(filteredFiles, category)
        this.setCache(cacheKey, tree)
        return tree
      }
    } catch (error) {
      console.warn('Failed to fetch manifest:', error)
    }

    // Fallback to mock data for development
    const mockTree = this.getMockFileTree(basePath)
    this.setCache(cacheKey, mockTree)
    return mockTree
  }

  /**
   * Fetches file content with proper error handling
   */
  async fetchFileContent(path: string): Promise<string> {
    const cacheKey = `content_${path}`
    const cached = this.getFromCache<string>(cacheKey)
    
    if (cached) {
      return cached
    }

    // Ensure path starts with resources/ if it doesn't
    let cleanPath = this.sanitizePath(path)
    if (!cleanPath.startsWith('resources/')) {
      cleanPath = cleanPath.replace(/^.*\/resources\//, 'resources/')
    }
    
    const response = await fetch(`${this.baseUrl}${cleanPath}`)
    
    if (!response.ok) {
      throw new Error(`Failed to fetch file: ${response.statusText}`)
    }
    
    const content = await response.text()
    this.setCache(cacheKey, content)
    return content
  }

  /**
   * Gets download URL for a file
   */
  getDownloadUrl(path: string): string {
    const cleanPath = this.sanitizePath(path)
    return `${this.baseUrl}${cleanPath}`
  }

  /**
   * Gets raw GitHub URL for direct access
   */
  getRawGitHubUrl(path: string): string {
    const cleanPath = this.sanitizePath(path)
    return `https://raw.githubusercontent.com/${this.githubRepo}/${this.githubBranch}/${cleanPath}`
  }

  /**
   * Sanitizes file path to prevent directory traversal attacks
   */
  private sanitizePath(path: string): string {
    // Remove leading slash and any directory traversal attempts
    return path
      .replace(/^\/+/, '')
      .replace(/\.\.+/g, '')
      .replace(/\/+/g, '/')
  }

  /**
   * Cache management with TTL
   */
  private getFromCache<T = unknown>(key: string): T | null {
    const cached = this.cache.get(key)
    if (!cached) return null
    
    const TTL = 5 * 60 * 1000 // 5 minutes
    if (Date.now() - cached.timestamp > TTL) {
      this.cache.delete(key)
      return null
    }
    
    return cached.data as T
  }

  private setCache<T = unknown>(key: string, data: T): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    })
  }

  /**
   * Transforms flat file list to hierarchical tree structure
   */
  private transformToFileTree(files: string[], category: string): FileNode[] {
    const root: Map<string, FileNode> = new Map()
    const tree: FileNode[] = []
    
    // First, ensure we have a root node for the category itself
    if (files.length > 0 && category) {
      const categoryNode: FileNode = {
        name: category,
        path: `resources/${category}`,
        type: 'directory',
        children: []
      }
      tree.push(categoryNode)
      root.set(`resources/${category}`, categoryNode)
    }
    
    files.sort() // Ensure consistent ordering
    
    files.forEach(filePath => {
      // Remove the category prefix to get the relative path
      const relativePath = filePath.startsWith(category + '/') 
        ? filePath.substring(category.length + 1)
        : filePath
      
      const parts = relativePath.split('/').filter(Boolean)
      let currentPath = `resources/${category}`
      let parentChildren = tree[0]?.children || tree
      
      parts.forEach((part, index) => {
        currentPath = `${currentPath}/${part}`
        const isFile = index === parts.length - 1 && part.includes('.')
        
        if (!root.has(currentPath)) {
          const node: FileNode = {
            name: part,
            path: currentPath,
            type: isFile ? 'file' : 'directory',
            extension: isFile ? part.split('.').pop() : undefined,
            language: isFile ? this.detectLanguage(part) : undefined
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

  /**
   * Language detection based on file extension
   */
  private detectLanguage(filename: string): string {
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

  /**
   * Mock data generator for development
   */
  private getMockFileTree(basePath: string): FileNode[] {
    return getMockFileTree(basePath)
  }
}