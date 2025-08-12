import { ref, computed } from 'vue'
import type { FileNode, NavigationState, BreadcrumbItem } from '@/types/resources'

export const useFileNavigation = () => {
  const navigationState = ref<NavigationState>({
    currentPath: [],
    selectedFile: null,
    expandedFolders: new Set(),
    history: []
  })

  const navigateToPath = (path: string[]) => {
    navigationState.value.history.push(navigationState.value.currentPath.join('/'))
    navigationState.value.currentPath = path
  }

  const selectFile = (file: FileNode) => {
    navigationState.value.selectedFile = file
    if (file.type === 'directory') {
      const pathSegments = file.path.split('/').filter(Boolean)
      navigateToPath(pathSegments)
    }
  }

  const toggleFolder = (path: string) => {
    const expanded = navigationState.value.expandedFolders
    if (expanded.has(path)) {
      expanded.delete(path)
    } else {
      expanded.add(path)
    }
  }

  const goBack = () => {
    const previousPath = navigationState.value.history.pop()
    if (previousPath) {
      navigationState.value.currentPath = previousPath.split('/').filter(Boolean)
    }
  }

  const breadcrumbs = computed<BreadcrumbItem[]>(() => {
    const items: BreadcrumbItem[] = [{ name: 'Home', path: '/' }]
    
    navigationState.value.currentPath.forEach((segment, index) => {
      items.push({
        name: segment,
        path: '/' + navigationState.value.currentPath.slice(0, index + 1).join('/')
      })
    })
    
    return items
  })

  const isExpanded = (path: string): boolean => {
    return navigationState.value.expandedFolders.has(path)
  }

  return {
    navigationState: computed(() => navigationState.value),
    navigateToPath,
    selectFile,
    toggleFolder,
    goBack,
    breadcrumbs,
    isExpanded
  }
}