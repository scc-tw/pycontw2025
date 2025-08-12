export interface FileNode {
  name: string
  path: string
  type: 'file' | 'directory'
  children?: FileNode[]
  size?: number
  language?: string
  lastModified?: string
  extension?: string
}

export interface ResourceMetadata {
  title: string
  description: string
  category: 'source' | 'data'
  tags: string[]
  createdAt: string
  updatedAt: string
}

export interface BenchmarkData {
  id: string
  name: string
  path: string
  type: 'csv' | 'json' | 'svg' | 'png' | 'yaml'
  metadata?: {
    tool?: string
    date?: string
    parameters?: Record<string, any>
    results?: Record<string, any>
  }
}

export interface SourceFile {
  path: string
  name: string
  language: 'python' | 'yaml' | 'json' | 'shell' | 'markdown' | string
  content?: string
  size: number
  downloadUrl: string
}

export interface NavigationState {
  currentPath: string[]
  selectedFile: FileNode | null
  expandedFolders: Set<string>
  history: string[]
}

export interface BreadcrumbItem {
  name: string
  path: string
}