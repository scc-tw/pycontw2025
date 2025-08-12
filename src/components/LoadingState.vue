<template>
  <div class="loading-state" :class="sizeClass">
    <div class="loading-spinner">
      <div class="spinner-circle"></div>
    </div>
    <p v-if="message" class="loading-message">{{ message }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  message?: string
  size?: 'small' | 'medium' | 'large' | 'full'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium'
})

const sizeClass = computed(() => `loading-${props.size}`)
</script>

<style scoped>
.loading-state {
  @apply flex flex-col items-center justify-center p-4;
}

.loading-small {
  @apply py-2;
}

.loading-medium {
  @apply py-8;
}

.loading-large {
  @apply py-16;
}

.loading-full {
  @apply min-h-screen;
}

.loading-spinner {
  @apply relative;
}

.spinner-circle {
  @apply w-12 h-12 border-4 border-gray-200 border-t-pycon-blue rounded-full animate-spin;
}

.loading-small .spinner-circle {
  @apply w-6 h-6 border-2;
}

.loading-large .spinner-circle,
.loading-full .spinner-circle {
  @apply w-16 h-16;
}

.loading-message {
  @apply mt-4 text-gray-600 text-sm;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>