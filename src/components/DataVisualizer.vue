<template>
  <div class="data-visualizer">
    <div class="viewer-header">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold">{{ file?.name || 'Select a data file' }}</h3>
        <div class="flex gap-2">
          <button
            v-if="file && canCopy"
            @click="copyToClipboard"
            class="btn-action"
            :title="copied ? 'Copied!' : 'Copy data'"
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
        Type: {{ getFileType(file) }}
        <span v-if="file.size" class="ml-3">Size: {{ formatFileSize(file.size) }}</span>
      </div>
    </div>
    
    <div class="viewer-content">
      <div v-if="loading" class="flex items-center justify-center h-64">
        <span class="text-gray-500">Loading data...</span>
      </div>
      
      <div v-else-if="error" class="error-message">
        Error loading file: {{ error }}
      </div>
      
      <div v-else-if="!file" class="empty-state">
        <p class="text-gray-500">Select a data file to view its contents</p>
      </div>
      
      <!-- SVG Display -->
      <div v-else-if="isSvg" class="svg-container">
        <div class="svg-controls">
          <button @click="zoomIn" class="zoom-btn">🔍+</button>
          <button @click="zoomOut" class="zoom-btn">🔍-</button>
          <button @click="resetZoom" class="zoom-btn">Reset</button>
        </div>
        <div 
          class="svg-content" 
          :style="{ transform: `scale(${zoomLevel})` }"
          v-html="content"
        ></div>
      </div>
      
      <!-- Image Display -->
      <div v-else-if="isImage" class="image-viewer">
        <img :src="imageUrl" :alt="file.name" class="max-w-full h-auto" />
      </div>
      
      <!-- PDF Display -->
      <div v-else-if="isPdf" class="pdf-viewer">
        <div class="pdf-notice">
          <h4 class="text-lg font-semibold mb-2">📄 PDF Document</h4>
          <p class="text-gray-600 mb-4">{{ file.name }}</p>
          <div class="flex gap-4">
            <a :href="imageUrl" target="_blank" class="pdf-action-btn">
              🔍 View in New Tab
            </a>
            <button @click="downloadFile" class="pdf-action-btn">
              ⬇️ Download PDF
            </button>
          </div>
        </div>
        <div class="pdf-embed mt-4">
          <embed :src="imageUrl" type="application/pdf" class="w-full h-96">
        </div>
      </div>
      
      <!-- JSON Display -->
      <div v-else-if="isJson" class="json-viewer">
        <pre class="json-content">{{ formattedJson }}</pre>
      </div>
      
      <!-- CSV Display -->
      <div v-else-if="isCsv" class="csv-viewer">
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th v-for="(header, index) in csvHeaders" :key="index">
                  {{ header }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, rowIndex) in csvData" :key="rowIndex">
                <td v-for="(cell, cellIndex) in row" :key="cellIndex">
                  {{ cell }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <!-- YAML Display -->
      <div v-else-if="isYaml" class="yaml-viewer">
        <pre class="yaml-content">{{ content }}</pre>
      </div>
      
      <!-- Markdown Display -->
      <div v-else-if="isMarkdown" class="markdown-viewer prose prose-sm max-w-none" v-html="renderedMarkdown"></div>
      
      <!-- Default text display -->
      <div v-else class="text-viewer">
        <pre class="text-content">{{ content || 'Empty file' }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { FileNode } from '@/types/resources'
import { formatFileSize } from '@/utils/fileHelpers'
import { useGitHubContent } from '@/composables/useGitHubContent'
import MarkdownIt from 'markdown-it'

interface Props {
  file: FileNode | null
}

const props = defineProps<Props>()

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

const { fetchFileContent, getDownloadUrl } = useGitHubContent()
const content = ref<string>('')
const loading = ref(false)
const error = ref<string | null>(null)
const copied = ref(false)
const zoomLevel = ref(1)

const csvHeaders = ref<string[]>([])
const csvData = ref<string[][]>([])

const getFileType = (file: FileNode): string => {
  const ext = file.extension?.toLowerCase()
  const typeMap: Record<string, string> = {
    'svg': 'SVG Vector Graphics',
    'png': 'PNG Image',
    'jpg': 'JPEG Image',
    'jpeg': 'JPEG Image',
    'json': 'JSON Data',
    'csv': 'CSV Table',
    'yaml': 'YAML Configuration',
    'yml': 'YAML Configuration',
    'md': 'Markdown Document',
    'txt': 'Plain Text',
    'pdf': 'PDF Document'
  }
  return typeMap[ext || ''] || 'Unknown'
}

const isImage = computed(() => {
  const imageExtensions = ['png', 'jpg', 'jpeg', 'gif', 'webp']
  return props.file?.extension && imageExtensions.includes(props.file.extension.toLowerCase())
})

const isSvg = computed(() => props.file?.extension?.toLowerCase() === 'svg')
const isJson = computed(() => props.file?.extension?.toLowerCase() === 'json')
const isCsv = computed(() => props.file?.extension?.toLowerCase() === 'csv')
const isYaml = computed(() => ['yaml', 'yml'].includes(props.file?.extension?.toLowerCase() || ''))
const isMarkdown = computed(() => props.file?.extension?.toLowerCase() === 'md')
const isPdf = computed(() => props.file?.extension?.toLowerCase() === 'pdf')

const canCopy = computed(() => !isImage.value)

const imageUrl = computed(() => {
  return props.file ? getDownloadUrl(props.file.path) : ''
})

const formattedJson = computed(() => {
  if (!isJson.value || !content.value) return ''
  try {
    return JSON.stringify(JSON.parse(content.value), null, 2)
  } catch {
    return content.value
  }
})

const renderedMarkdown = computed(() => {
  if (!isMarkdown.value || !content.value) return ''
  return md.render(content.value)
})

const parseCsv = (text: string) => {
  const lines = text.trim().split('\n')
  if (lines.length === 0) return
  
  csvHeaders.value = lines[0].split(',').map(h => h.trim())
  csvData.value = lines.slice(1).map(line => 
    line.split(',').map(cell => cell.trim())
  )
}

watch(() => props.file, async (newFile) => {
  if (!newFile || newFile.type === 'directory') {
    content.value = ''
    csvHeaders.value = []
    csvData.value = []
    return
  }
  
  if (isImage.value) {
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    content.value = await fetchFileContent(newFile.path)
    
    if (isCsv.value) {
      parseCsv(content.value)
    }
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

const zoomIn = () => {
  zoomLevel.value = Math.min(zoomLevel.value + 0.25, 3)
}

const zoomOut = () => {
  zoomLevel.value = Math.max(zoomLevel.value - 0.25, 0.5)
}

const resetZoom = () => {
  zoomLevel.value = 1
}
</script>

<style scoped>
.data-visualizer {
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

.empty-state {
  @apply flex items-center justify-center h-64;
}

.error-message {
  @apply p-4 text-red-600 bg-red-50;
}

.svg-container {
  @apply relative;
}

.svg-controls {
  @apply absolute top-4 right-4 z-10 flex gap-2;
}

.zoom-btn {
  @apply px-2 py-1 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50;
}

.svg-content {
  @apply p-4 transition-transform origin-center;
}

.svg-content :deep(svg) {
  @apply max-w-full h-auto;
}

.image-viewer {
  @apply p-4 flex items-center justify-center;
}

.json-viewer, .yaml-viewer, .text-viewer {
  @apply p-4;
}

.json-content, .yaml-content, .text-content {
  @apply text-sm font-mono bg-gray-50 p-4 rounded overflow-x-auto;
}

.csv-viewer {
  @apply p-4;
}

.table-container {
  @apply overflow-x-auto;
}

.data-table {
  @apply min-w-full border-collapse;
}

.data-table th {
  @apply px-4 py-2 bg-gray-100 border border-gray-300 text-left font-semibold text-sm;
}

.data-table td {
  @apply px-4 py-2 border border-gray-300 text-sm;
}

.data-table tbody tr:hover {
  @apply bg-gray-50;
}

.markdown-viewer {
  @apply p-4;
}

.pdf-viewer {
  @apply p-4;
}

.pdf-notice {
  @apply bg-gray-50 border border-gray-200 rounded-lg p-4;
}

.pdf-action-btn {
  @apply px-4 py-2 bg-pycon-blue text-white rounded hover:bg-opacity-90 transition-colors text-sm font-medium;
}

.pdf-embed {
  @apply border border-gray-300 rounded;
}

.pdf-embed embed {
  @apply min-h-96;
}
</style>