<template>
  <div v-if="hasError" class="error-boundary">
    <div class="error-container">
      <div class="error-icon">⚠️</div>
      <h2 class="error-title">Something went wrong</h2>
      <p class="error-message">{{ errorMessage }}</p>
      <div class="error-actions">
        <button @click="retry" class="btn-retry">
          🔄 Try Again
        </button>
        <button @click="goHome" class="btn-home">
          🏠 Go Home
        </button>
      </div>
      <details v-if="isDevelopment" class="error-details">
        <summary>Error Details</summary>
        <pre>{{ errorStack }}</pre>
      </details>
    </div>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ServiceContainer } from '@/services/ServiceContainer'
import type { IErrorService } from '@/services/ErrorService'

interface Props {
  fallback?: string
  onError?: (error: Error) => void
}

const props = withDefaults(defineProps<Props>(), {
  fallback: 'An unexpected error occurred'
})

const router = useRouter()
const container = ServiceContainer.getInstance()
const configService = container.getConfigService()
const errorService = container.get<IErrorService>('ErrorService')

const hasError = ref(false)
const errorMessage = ref('')
const errorStack = ref('')
const isDevelopment = computed(() => configService.isDevelopment())

/**
 * Capture errors from child components
 */
onErrorCaptured((error: Error) => {
  hasError.value = true
  errorMessage.value = error.message || props.fallback
  errorStack.value = error.stack || ''
  
  // Log error through error service
  if (errorService) {
    errorService.handleError(error)
  }
  
  // Call custom error handler if provided
  if (props.onError) {
    props.onError(error)
  }
  
  // Prevent error from propagating
  return false
})

/**
 * Retry by resetting error state
 */
const retry = () => {
  hasError.value = false
  errorMessage.value = ''
  errorStack.value = ''
}

/**
 * Navigate to home page
 */
const goHome = () => {
  hasError.value = false
  router.push('/')
}
</script>

<style scoped>
.error-boundary {
  @apply min-h-screen flex items-center justify-center bg-gray-50 p-4;
}

.error-container {
  @apply max-w-lg w-full bg-white rounded-lg shadow-lg p-8 text-center;
}

.error-icon {
  @apply text-6xl mb-4;
}

.error-title {
  @apply text-2xl font-bold text-gray-800 mb-2;
}

.error-message {
  @apply text-gray-600 mb-6;
}

.error-actions {
  @apply flex gap-4 justify-center mb-6;
}

.btn-retry, .btn-home {
  @apply px-4 py-2 rounded font-medium transition-colors;
}

.btn-retry {
  @apply bg-pycon-blue text-white hover:bg-opacity-90;
}

.btn-home {
  @apply bg-gray-200 text-gray-700 hover:bg-gray-300;
}

.error-details {
  @apply text-left mt-6 p-4 bg-gray-100 rounded;
}

.error-details summary {
  @apply cursor-pointer font-medium text-gray-700;
}

.error-details pre {
  @apply mt-2 text-xs text-gray-600 whitespace-pre-wrap break-words;
}
</style>