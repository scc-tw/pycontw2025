import { ref } from 'vue'
import type { FileNode } from '@/types/resources'
import { buildFileTree } from '@/utils/fileHelpers'

export const useGitHubContent = () => {
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchFileTree = async (basePath: string): Promise<FileNode[]> => {
    loading.value = true
    error.value = null
    
    try {
      const tree = await buildFileTree(basePath)
      return tree
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch file tree'
      return []
    } finally {
      loading.value = false
    }
  }

  const fetchFileContent = async (path: string): Promise<string> => {
    loading.value = true
    error.value = null
    
    try {
      // Remove leading slash if present
      const cleanPath = path.startsWith('/') ? path.slice(1) : path
      const response = await fetch(`/${cleanPath}`)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch file: ${response.statusText}`)
      }
      
      return await response.text()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch file content'
      return ''
    } finally {
      loading.value = false
    }
  }

  const getDownloadUrl = (path: string): string => {
    // For GitHub Pages, files are served directly
    const cleanPath = path.startsWith('/') ? path.slice(1) : path
    return `/${cleanPath}`
  }

  const getRawGitHubUrl = (path: string): string => {
    // For direct GitHub raw content access
    const repo = 'pycontw2025'
    const branch = 'gh-pages'
    const cleanPath = path.startsWith('/') ? path.slice(1) : path
    return `https://raw.githubusercontent.com/${repo}/${branch}/${cleanPath}`
  }

  return {
    loading,
    error,
    fetchFileTree,
    fetchFileContent,
    getDownloadUrl,
    getRawGitHubUrl
  }
}