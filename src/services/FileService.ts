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
        const tree = this.transformToFileTree(manifest.files || [], basePath)
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

    const cleanPath = this.sanitizePath(path)
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
  private transformToFileTree(files: string[], basePath: string): FileNode[] {
    const root: Map<string, FileNode> = new Map()
    const tree: FileNode[] = []
    
    files.sort() // Ensure consistent ordering
    
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
      'pdf': 'pdf',
      'txt': 'text',
      'html': 'html',
      'css': 'css',
      'scss': 'scss',
      'vue': 'vue'
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