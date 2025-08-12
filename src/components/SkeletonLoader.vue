<template>
  <div class="skeleton-loader">
    <div
      v-for="i in lines"
      :key="i"
      class="skeleton-line"
      :style="{ width: getLineWidth(i) }"
    ></div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  lines?: number
  type?: 'text' | 'card' | 'table' | 'tree'
}

const props = withDefaults(defineProps<Props>(), {
  lines: 3,
  type: 'text'
})

const getLineWidth = (index: number): string => {
  if (props.type === 'text') {
    // Vary line widths for more natural look
    const widths = ['100%', '85%', '70%', '90%', '75%']
    return widths[index % widths.length]
  }
  
  if (props.type === 'tree') {
    // Indent for tree structure
    const indent = (index % 3) * 20
    return `calc(100% - ${indent}px)`
  }
  
  return '100%'
}
</script>

<style scoped>
.skeleton-loader {
  @apply space-y-3;
}

.skeleton-line {
  @apply h-4 bg-gray-200 rounded animate-pulse;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}
</style>