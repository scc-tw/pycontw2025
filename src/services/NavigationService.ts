import { reactive } from 'vue'
import type { FileNode, NavigationState, BreadcrumbItem } from '@/types/resources'

/**
 * Service for managing navigation state and history
 * Follows Single Responsibility Principle
 */
export interface INavigationService {
  getCurrentState(): NavigationState
  navigateToPath(path: string[]): void
  selectFile(file: FileNode): void
  toggleFolder(path: string): void
  goBack(): boolean
  getBreadcrumbs(): BreadcrumbItem[]
  isExpanded(path: string): boolean
  clearHistory(): void
}

export class NavigationService implements INavigationService {
  private state: NavigationState
  private readonly maxHistorySize = 50

  constructor() {
    this.state = reactive(this.initializeState())
  }

  /**
   * Initialize navigation state
   */
  private initializeState(): NavigationState {
    return {
      currentPath: [],
      selectedFile: null,
      expandedFolders: new Set(),
      history: []
    }
  }

  /**
   * Get current navigation state
   */
  getCurrentState(): NavigationState {
    return {
      ...this.state,
      expandedFolders: new Set(this.state.expandedFolders)
    }
  }

  /**
   * Navigate to a specific path
   */
  navigateToPath(path: string[]): void {
    // Save current path to history
    if (this.state.currentPath.length > 0) {
      this.addToHistory(this.state.currentPath.join('/'))
    }
    
    this.state.currentPath = [...path]
  }

  /**
   * Select a file or folder
   */
  selectFile(file: FileNode): void {
    this.state.selectedFile = file
    
    if (file.type === 'directory') {
      const pathSegments = file.path.split('/').filter(Boolean)
      this.navigateToPath(pathSegments)
      // Don't toggle here - let the toggle event handle it
    }
  }

  /**
   * Toggle folder expansion state
   */
  toggleFolder(path: string): void {
    if (this.state.expandedFolders.has(path)) {
      this.state.expandedFolders.delete(path)
    } else {
      this.state.expandedFolders.add(path)
    }
  }

  /**
   * Navigate back in history
   */
  goBack(): boolean {
    if (this.state.history.length === 0) {
      return false
    }
    
    const previousPath = this.state.history.pop()
    if (previousPath) {
      this.state.currentPath = previousPath.split('/').filter(Boolean)
      return true
    }
    
    return false
  }

  /**
   * Generate breadcrumb navigation items
   */
  getBreadcrumbs(): BreadcrumbItem[] {
    const items: BreadcrumbItem[] = [
      { name: 'Home', path: '/' }
    ]
    
    this.state.currentPath.forEach((segment, index) => {
      items.push({
        name: segment,
        path: '/' + this.state.currentPath.slice(0, index + 1).join('/')
      })
    })
    
    return items
  }

  /**
   * Check if a folder is expanded
   */
  isExpanded(path: string): boolean {
    return this.state.expandedFolders.has(path)
  }

  /**
   * Clear navigation history
   */
  clearHistory(): void {
    this.state.history = []
  }

  /**
   * Add path to history with size limit
   */
  private addToHistory(path: string): void {
    this.state.history.push(path)
    
    // Maintain history size limit
    if (this.state.history.length > this.maxHistorySize) {
      this.state.history.shift()
    }
  }
}