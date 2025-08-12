<template>
  <div class="source-code-view">
    <header class="view-header">
      <div class="container mx-auto px-4">
        <nav class="breadcrumb">
          <router-link
            v-for="(crumb, index) in breadcrumbs"
            :key="crumb.path"
            :to="index === 0 ? '/' : `/source${crumb.path}`"
            class="breadcrumb-item"
          >
            {{ crumb.name }}
            <span v-if="index < breadcrumbs.length - 1" class="breadcrumb-separator">/</span>
          </router-link>
        </nav>
      </div>
    </header>
    
    <div class="container mx-auto px-4 py-6">
      <div class="grid grid-cols-12 gap-6">
        <aside class="col-span-12 md:col-span-4 lg:col-span-3">
          <div class="sidebar-card">
            <h2 class="sidebar-title">📁 File Explorer</h2>
            <div class="sidebar-content">
              <FolderTree
                v-if="fileTree.length"
                :nodes="fileTree"
                :selected-path="navigationState.selectedFile?.path"
                :expanded-paths="navigationState.expandedFolders"
                @select="selectFile"
                @toggle="toggleFolder"
              />
              <LoadingState 
                v-else-if="loading" 
                message="Loading files..."
                size="small"
              />
              <div v-else-if="error" class="text-center py-4 text-red-500">
                {{ error }}
              </div>
              <div v-else class="text-center py-4 text-gray-500">
                No files found
              </div>
            </div>
          </div>
        </aside>
        
        <main class="col-span-12 md:col-span-8 lg:col-span-9">
          <CodeViewer :file="navigationState.selectedFile" />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import type { FileNode } from '@/types/resources'
import FolderTree from '@/components/FolderTree.vue'
import CodeViewer from '@/components/CodeViewer.vue'
import LoadingState from '@/components/LoadingState.vue'
import { useServices } from '@/composables/useServices'

const { fileService, navigationService, performanceService } = useServices()

const fileTree = ref<FileNode[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// Reactive navigation state
const navigationState = computed(() => navigationService.getCurrentState())
const breadcrumbs = computed(() => navigationService.getBreadcrumbs())

const selectFile = (file: FileNode) => {
  navigationService.selectFile(file)
}

const toggleFolder = (path: string) => {
  navigationService.toggleFolder(path)
}

onMounted(async () => {
  loading.value = true
  error.value = null
  
  try {
    await performanceService.measureAsync('fetchSourceTree', async () => {
      fileTree.value = await fileService.fetchFileTree('resources/source')
    })
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load files'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.source-code-view {
  @apply min-h-screen bg-gray-50;
}

.view-header {
  @apply bg-white border-b border-gray-200 py-3;
}

.breadcrumb {
  @apply flex items-center space-x-1 text-sm;
}

.breadcrumb-item {
  @apply text-gray-600 hover:text-pycon-blue transition-colors;
}

.breadcrumb-item:last-child {
  @apply text-pycon-blue font-medium;
}

.breadcrumb-separator {
  @apply mx-1 text-gray-400;
}

.sidebar-card {
  @apply bg-white rounded-lg shadow-sm border border-gray-200;
}

.sidebar-title {
  @apply px-4 py-3 border-b border-gray-200 font-semibold text-pycon-blue;
}

.sidebar-content {
  @apply p-4 max-h-[calc(100vh-200px)] overflow-y-auto;
}
</style>