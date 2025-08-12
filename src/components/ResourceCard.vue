<template>
  <router-link
    :to="to"
    class="resource-card"
  >
    <div class="card-icon">
      {{ icon }}
    </div>
    <div class="card-content">
      <h3 class="card-title">{{ title }}</h3>
      <p class="card-description">{{ description }}</p>
      <div class="card-footer">
        <span class="card-count">{{ fileCount }} files</span>
        <span class="card-arrow">→</span>
      </div>
    </div>
  </router-link>
</template>

<script setup lang="ts">
interface Props {
  title: string
  description: string
  icon: string
  to: string
  fileCount: number
}

defineProps<Props>()
</script>

<style scoped>
.resource-card {
  @apply block bg-white rounded-lg shadow-md border border-gray-200 p-6 hover:shadow-lg transition-shadow cursor-pointer;
}

.card-icon {
  @apply text-4xl mb-4;
}

.card-content {
  @apply space-y-2;
}

.card-title {
  @apply text-xl font-bold text-pycon-blue;
}

.card-description {
  @apply text-gray-600 text-sm;
}

.card-footer {
  @apply flex items-center justify-between mt-4 pt-4 border-t border-gray-100;
}

.card-count {
  @apply text-sm text-gray-500;
}

.card-arrow {
  @apply text-pycon-light-blue text-xl;
}
</style>