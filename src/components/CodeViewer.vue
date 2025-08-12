<template>
  <div class="code-viewer">
    <div class="viewer-header">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold">{{ file?.name || 'Select a file' }}</h3>
        <div class="flex gap-2">
          <button
            v-if="file"
            @click="copyToClipboard"
            class="btn-action"
            :title="copied ? 'Copied!' : 'Copy to clipboard'"
          >
            {{ copied ? '✓' : '📋' }} {{ copied ? 'Copied' : 'Copy' }}
          </button>
          <button
            v-if="file"
            @click="downloadFile"
            class="btn-action"
            title="Download file"
          >
            ⬇️ Download
          </button>
        </div>
      </div>
      <div v-if="file" class="text-sm text-gray-500 mt-1">
        Language: {{ file.language || 'plain text' }}
        <span v-if="file.size" class="ml-3">Size: {{ formatFileSize(file.size) }}</span>
      </div>
    </div>
    
    <div class="viewer-content">
      <div v-if="loading" class="flex items-center justify-center h-64">
        <span class="text-gray-500">Loading...</span>
      </div>
      
      <div v-else-if="error" class="error-message">
        Error loading file: {{ error }}
      </div>
      
      <div v-else-if="!file" class="empty-state">
        <p class="text-gray-500">Select a file from the tree to view its contents</p>
      </div>
      
      <div v-else-if="isImage" class="image-viewer">
        <img :src="imageUrl" :alt="file.name" class="max-w-full h-auto" />
      </div>
      
      <div v-else-if="isSvg" class="svg-viewer" v-html="content"></div>
      
      <pre v-else class="code-content"><code>{{ content || 'Empty file' }}</code></pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { FileNode } from '@/types/resources'
import { formatFileSize } from '@/utils/fileHelpers'
import { useGitHubContent } from '@/composables/useGitHubContent'

interface Props {
  file: FileNode | null
}

const props = defineProps<Props>()

const { fetchFileContent, getDownloadUrl } = useGitHubContent()
const content = ref<string>('')
const loading = ref(false)
const error = ref<string | null>(null)
const copied = ref(false)

const isImage = computed(() => {
  const imageExtensions = ['png', 'jpg', 'jpeg', 'gif', 'webp']
  return props.file?.extension && imageExtensions.includes(props.file.extension.toLowerCase())
})

const isSvg = computed(() => {
  return props.file?.extension?.toLowerCase() === 'svg'
})

const imageUrl = computed(() => {
  return props.file ? getDownloadUrl(props.file.path) : ''
})

watch(() => props.file, async (newFile) => {
  if (!newFile || newFile.type === 'directory') {
    content.value = ''
    return
  }
  
  if (isImage.value) {
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    content.value = await fetchFileContent(newFile.path)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load file'
  } finally {
    loading.value = false
  }
}, { immediate: true })

const copyToClipboard = async () => {
  if (!content.value) return
  
  try {
    await navigator.clipboard.writeText(content.value)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (e) {
    console.error('Failed to copy:', e)
  }
}

const downloadFile = () => {
  if (!props.file) return
  
  const url = getDownloadUrl(props.file.path)
  const link = document.createElement('a')
  link.href = url
  link.download = props.file.name
  link.click()
}
</script>

<style scoped>
.code-viewer {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 h-full flex flex-col;
}

.viewer-header {
  @apply p-4 border-b border-gray-200;
}

.viewer-content {
  @apply flex-1 overflow-auto;
}

.btn-action {
  @apply px-3 py-1 text-sm bg-pycon-blue text-white rounded hover:bg-opacity-90 transition-colors;
}

.code-content {
  @apply p-4 text-sm font-mono bg-gray-50 min-h-full;
}

.empty-state {
  @apply flex items-center justify-center h-64;
}

.error-message {
  @apply p-4 text-red-600 bg-red-50;
}

.image-viewer {
  @apply p-4 flex items-center justify-center;
}

.svg-viewer {
  @apply p-4;
}

.svg-viewer :deep(svg) {
  @apply max-w-full h-auto;
}
</style>