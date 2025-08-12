<template>
  <div class="benchmark-data-view">
    <header class="view-header">
      <div class="container mx-auto px-4">
        <nav class="breadcrumb">
          <router-link
            v-for="(crumb, index) in breadcrumbs"
            :key="crumb.path"
            :to="index === 0 ? '/' : `/data${crumb.path}`"
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
            <h2 class="sidebar-title">📊 Data Explorer</h2>
            <div class="sidebar-content">
              <FolderTree
                v-if="fileTree.length"
                :nodes="fileTree"
                :selected-path="navigationState.selectedFile?.path"
                :expanded-paths="navigationState.expandedFolders"
                @select="selectFile"
                @toggle="toggleFolder"
              />
              <div v-else-if="loading" class="text-center py-4 text-gray-500">
                Loading data files...
              </div>
              <div v-else class="text-center py-4 text-gray-500">
                No data files found
              </div>
            </div>
          </div>
        </aside>
        
        <main class="col-span-12 md:col-span-8 lg:col-span-9">
          <DataVisualizer :file="navigationState.selectedFile" />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { FileNode } from '@/types/resources'
import FolderTree from '@/components/FolderTree.vue'
import DataVisualizer from '@/components/DataVisualizer.vue'
import { useFileNavigation } from '@/composables/useFileNavigation'
import { useGitHubContent } from '@/composables/useGitHubContent'

const {
  navigationState,
  selectFile,
  toggleFolder,
  breadcrumbs
} = useFileNavigation()

const { fetchFileTree, loading } = useGitHubContent()
const fileTree = ref<FileNode[]>([])

onMounted(async () => {
  fileTree.value = await fetchFileTree('resources/data')
})
</script>

<style scoped>
.benchmark-data-view {
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