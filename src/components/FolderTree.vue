<template>
  <div class="folder-tree" role="tree" :aria-label="`File tree level ${level + 1}`">
    <div
      v-for="(node, index) in nodes"
      :key="node.path"
      class="tree-node"
      role="treeitem"
      :aria-expanded="node.type === 'directory' ? isExpanded(node.path) : undefined"
      :aria-selected="selectedPath === node.path"
      :aria-level="level + 1"
      :aria-setsize="nodes.length"
      :aria-posinset="index + 1"
    >
      <div
        class="node-item"
        :class="{
          'node-directory': node.type === 'directory',
          'node-file': node.type === 'file',
          'node-selected': selectedPath === node.path,
          'ml-4': level > 0
        }"
        :tabindex="selectedPath === node.path ? 0 : -1"
        @click="handleNodeClick(node)"
        @keydown="handleKeyDown($event, node)"
      >
        <span class="node-icon">
          <span v-if="node.type === 'directory'">
            {{ isExpanded(node.path) ? '📂' : '📁' }}
          </span>
          <span v-else>{{ getFileIcon(node) }}</span>
        </span>
        <span class="node-name">{{ node.name }}</span>
        <span v-if="node.extension" class="node-extension text-gray-500 text-sm ml-1">
          .{{ node.extension }}
        </span>
      </div>
      
      <div v-if="node.type === 'directory' && node.children && isExpanded(node.path)" class="ml-2">
        <FolderTree
          :nodes="node.children"
          :selected-path="selectedPath"
          :level="level + 1"
          :expanded-paths="expandedPaths"
          @select="$emit('select', $event)"
          @toggle="$emit('toggle', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FileNode } from '@/types/resources'
import { getFileIcon } from '@/utils/fileHelpers'

interface Props {
  nodes: FileNode[]
  selectedPath?: string
  level?: number
  expandedPaths?: Set<string>
}

const props = withDefaults(defineProps<Props>(), {
  level: 0,
  expandedPaths: () => new Set()
})

const emit = defineEmits<{
  select: [node: FileNode]
  toggle: [path: string]
}>()

const isExpanded = (path: string): boolean => {
  return props.expandedPaths?.has(path) ?? false
}

const handleNodeClick = (node: FileNode) => {
  if (node.type === 'directory') {
    emit('toggle', node.path)
  }
  emit('select', node)
}

const handleKeyDown = (event: KeyboardEvent, node: FileNode) => {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    handleNodeClick(node)
  } else if (event.key === 'ArrowRight' && node.type === 'directory') {
    // Expand directory
    if (!isExpanded(node.path)) {
      emit('toggle', node.path)
    }
  } else if (event.key === 'ArrowLeft' && node.type === 'directory') {
    // Collapse directory
    if (isExpanded(node.path)) {
      emit('toggle', node.path)
    }
  }
}
</script>

<style scoped>
.folder-tree {
  @apply space-y-1;
}

.node-item {
  @apply flex items-center px-2 py-1 rounded cursor-pointer hover:bg-gray-100 transition-colors;
}

.node-item.node-selected {
  @apply bg-pycon-light-blue bg-opacity-20;
}

.node-icon {
  @apply mr-2 text-lg;
}

.node-name {
  @apply text-sm font-medium;
}

.node-directory .node-name {
  @apply text-gray-700;
}

.node-file .node-name {
  @apply text-gray-600;
}
</style>