<template>
  <div class="home-page">
    <header class="hero-section">
      <div class="container mx-auto px-4">
        <h1 class="hero-title">PyCon TW 2025</h1>
        <h2 class="hero-subtitle">Resource Assets & Benchmarks</h2>
        <p class="hero-description">
          Access source code, benchmark data, and visualizations from the presentation
        </p>
      </div>
    </header>
    
    <main class="container mx-auto px-4 py-12">
      <div class="grid md:grid-cols-2 gap-8">
        <ResourceCard
          title="Source Code"
          description="Browse and download benchmark scripts, test files, and implementation code"
          icon="💻"
          to="/source"
          :file-count="sourceFileCount"
        />
        
        <ResourceCard
          title="Benchmark Data"
          description="Explore performance metrics, visualizations, and analysis results"
          icon="📊"
          to="/data"
          :file-count="dataFileCount"
        />
      </div>
      
      <section class="mt-16">
        <h3 class="text-2xl font-bold text-pycon-blue mb-6">Quick Links</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <a href="https://github.com/scc-tw/pycontw2025" target="_blank" class="quick-link">
            📦 GitHub Repository
          </a>
          <router-link to="/data/slides" class="quick-link">
            📹 Presentation Slides
          </router-link>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ResourceCard from '@/components/ResourceCard.vue'

const sourceFileCount = ref(0)
const dataFileCount = ref(0)

onMounted(async () => {
  // In production, fetch actual file counts
  // For now, using placeholder values
  sourceFileCount.value = 42
  dataFileCount.value = 28
})
</script>

<style scoped>
.home-page {
  @apply min-h-screen bg-gray-50;
}

.hero-section {
  @apply bg-gradient-to-r from-pycon-blue to-pycon-light-blue text-white py-16;
}

.hero-title {
  @apply text-5xl font-bold mb-2;
}

.hero-subtitle {
  @apply text-3xl font-semibold mb-4 text-pycon-gold;
}

.hero-description {
  @apply text-xl opacity-90;
}

.quick-link {
  @apply flex items-center justify-center p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow text-pycon-blue font-medium;
}
</style>