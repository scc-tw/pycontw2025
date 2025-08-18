<template>
  <div class="data-visualizer">
    <!-- JSON Data Viewer -->
    <div v-if="isJson" class="json-viewer">
      <pre class="json-content">{{ formattedJson }}</pre>
    </div>

    <!-- CSV/TSV Table Viewer -->
    <div v-else-if="isCsv || isTsv" class="table-viewer">
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th v-for="header in tableHeaders" :key="header">{{ header }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in tableRows" :key="index">
              <td v-for="header in tableHeaders" :key="header">{{ row[header] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Image Viewer (PNG, SVG) -->
    <div v-else-if="isImage" class="image-viewer">
      <img :src="fileUrl" :alt="fileName" class="visualization-image" />
    </div>

    <!-- SVG Viewer -->
    <div v-else-if="isSvg" class="svg-viewer">
      <div class="svg-controls">
        <button @click="openFullPage" class="btn-fullpage" title="Open in full page">
          <span class="icon">⤢</span> View Full Page
        </button>
      </div>
      <div v-if="content" v-html="content" class="svg-container"></div>
      <div v-else class="svg-container">
        <object :data="fileUrl" type="image/svg+xml" class="svg-object">
          <img :src="fileUrl" :alt="fileName" class="svg-fallback" />
        </object>
      </div>
    </div>

    <!-- Performance Data Viewer -->
    <div v-else-if="isPerfData" class="perf-viewer">
      <div class="perf-info">
        <div class="info-icon">⚡</div>
        <h3>Performance Profile Data</h3>
        <p>{{ fileName }}</p>
        <div class="perf-actions">
          <button @click="downloadFile" class="btn-download">
            📥 Download Raw Data
          </button>
          <p class="perf-note">
            Use perf report or flamegraph tools to analyze this data
          </p>
        </div>
      </div>
    </div>

    <!-- PDF Viewer -->
    <div v-else-if="isPdf" class="pdf-viewer">
      <div class="pdf-info">
        <div class="info-icon">📕</div>
        <h3>PDF Document</h3>
        <p>{{ fileName }}</p>
        <div class="pdf-actions">
          <a :href="fileUrl" target="_blank" class="btn-view">
            👁️ View PDF
          </a>
          <button @click="downloadFile" class="btn-download">
            📥 Download PDF
          </button>
        </div>
      </div>
    </div>

    <!-- Text/Markdown Viewer -->
    <div v-else-if="isText || isMarkdown" class="text-viewer">
      <div v-if="isMarkdown" v-html="renderedMarkdown" class="markdown-content"></div>
      <pre v-else class="text-content">{{ content }}</pre>
    </div>

    <!-- Binary/Unknown File -->
    <div v-else class="binary-viewer">
      <div class="binary-info">
        <div class="info-icon">📦</div>
        <h3>Binary File</h3>
        <p>{{ fileName }}</p>
        <p class="file-size">Size: {{ formatFileSize(fileSize) }}</p>
        <button @click="downloadFile" class="btn-download">
          📥 Download File
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { FileNode } from '@/types/resources'
import { formatFileSize } from '@/utils/fileHelpers'
// import { useServices } from '@/composables/useServices' // Reserved for future use

interface Props {
  file: FileNode
  content?: string
  fileUrl?: string
  fileSize?: number
}

const props = defineProps<Props>()
// const { fileService } = useServices() // Reserved for future use

const fileName = computed(() => props.file.name)
const fileExtension = computed(() => props.file.extension?.toLowerCase() || '')

// File type checks
const isJson = computed(() => fileExtension.value === 'json')
const isCsv = computed(() => fileExtension.value === 'csv')
const isTsv = computed(() => fileExtension.value === 'tsv')
const isImage = computed(() => ['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(fileExtension.value))
const isSvg = computed(() => fileExtension.value === 'svg')
const isPerfData = computed(() => ['data', 'perf'].includes(fileExtension.value))
const isPdf = computed(() => fileExtension.value === 'pdf')
const isText = computed(() => ['txt', 'log', 'out'].includes(fileExtension.value))
const isMarkdown = computed(() => ['md', 'mdx'].includes(fileExtension.value))

// JSON formatting
const formattedJson = computed(() => {
  if (!isJson.value || !props.content) return ''
  try {
    const parsed = JSON.parse(props.content)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return props.content
  }
})

// CSV/TSV parsing
const tableHeaders = ref<string[]>([])
const tableRows = ref<Record<string, string>[]>([])

const parseTableData = (content: string, delimiter: string) => {
  const lines = content.trim().split('\n')
  if (lines.length === 0) return

  // Parse headers
  tableHeaders.value = lines[0].split(delimiter).map(h => h.trim())

  // Parse rows
  tableRows.value = lines.slice(1).map(line => {
    const values = line.split(delimiter)
    const row: Record<string, string> = {}
    tableHeaders.value.forEach((header, index) => {
      row[header] = values[index]?.trim() || ''
    })
    return row
  })
}

// Markdown rendering (simplified - in production, use markdown-it)
const renderedMarkdown = computed(() => {
  if (!isMarkdown.value || !props.content) return ''
  
  // Very basic markdown rendering
  let html = props.content
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*)\*/g, '<em>$1</em>')
    .replace(/```[\s\S]*?```/g, (match) => {
      const code = match.replace(/```/g, '')
      return `<pre><code>${code}</code></pre>`
    })
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
  
  return html
})

// Watch for content changes
watch(() => props.content, (newContent) => {
  if (newContent) {
    if (isCsv.value) {
      parseTableData(newContent, ',')
    } else if (isTsv.value) {
      parseTableData(newContent, '\t')
    }
  }
}, { immediate: true })

// Open SVG in full page
const openFullPage = () => {
  if (props.fileUrl) {
    window.open(props.fileUrl, '_blank')
  }
}

// Download functionality
const downloadFile = () => {
  if (!props.fileUrl) return
  
  const link = document.createElement('a')
  link.href = props.fileUrl
  link.download = fileName.value
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>

<style scoped>
.data-visualizer {
  @apply bg-white rounded-lg shadow-sm p-4;
}

/* JSON Viewer */
.json-viewer {
  @apply overflow-auto;
}

.json-content {
  @apply text-sm font-mono bg-gray-50 p-4 rounded overflow-x-auto;
  max-height: 600px;
}

/* Table Viewer */
.table-container {
  @apply overflow-auto;
  max-height: 600px;
}

.data-table {
  @apply w-full text-sm;
}

.data-table th {
  @apply bg-gray-100 px-4 py-2 text-left font-semibold sticky top-0;
}

.data-table td {
  @apply px-4 py-2 border-b border-gray-200;
}

.data-table tr:hover {
  @apply bg-gray-50;
}

/* Image Viewer */
.image-viewer {
  @apply flex justify-center items-center p-4;
}

.visualization-image {
  @apply max-w-full h-auto rounded shadow-md;
  max-height: 600px;
}

/* SVG Viewer */
.svg-viewer {
  @apply relative;
}

.svg-controls {
  @apply flex justify-end p-2 border-b border-gray-200;
}

.btn-fullpage {
  @apply inline-flex items-center px-3 py-1.5 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors;
}

.btn-fullpage .icon {
  @apply mr-1 text-lg;
}

.svg-container {
  @apply flex justify-center items-center p-4;
  max-height: 600px;
  overflow: auto;
}

.svg-container :deep(svg) {
  @apply max-w-full h-auto;
}

.svg-object {
  @apply max-w-full h-auto;
  max-height: 580px;
}

.svg-fallback {
  @apply max-w-full h-auto;
}

/* Performance Data Viewer */
.perf-viewer, .pdf-viewer, .binary-viewer {
  @apply flex flex-col items-center justify-center py-12;
}

.perf-info, .pdf-info, .binary-info {
  @apply text-center;
}

.info-icon {
  @apply text-6xl mb-4;
}

.perf-actions, .pdf-actions {
  @apply mt-6 space-y-4;
}

.perf-note {
  @apply text-sm text-gray-600 mt-4;
}

.file-size {
  @apply text-sm text-gray-600 mt-2;
}

/* Text/Markdown Viewer */
.text-content {
  @apply text-sm font-mono bg-gray-50 p-4 rounded overflow-auto;
  max-height: 600px;
}

.markdown-content {
  @apply text-sm leading-relaxed;
  max-height: 600px;
  overflow-y: auto;
}

.markdown-content :deep(h1) {
  @apply text-2xl font-bold mb-4;
}

.markdown-content :deep(h2) {
  @apply text-xl font-bold mb-3;
}

.markdown-content :deep(h3) {
  @apply text-lg font-bold mb-2;
}

.markdown-content :deep(pre) {
  @apply bg-gray-100 p-3 rounded overflow-x-auto;
}

.markdown-content :deep(code) {
  @apply bg-gray-100 px-1 py-0.5 rounded text-sm;
}

/* Buttons */
.btn-download, .btn-view {
  @apply inline-flex items-center px-4 py-2 bg-pycon-blue text-white rounded hover:bg-opacity-90 transition-colors;
}

.btn-view {
  @apply mr-4;
}
</style>