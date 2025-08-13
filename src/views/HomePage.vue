<template>
  <div class="home-page">
    <header class="hero-section">
      <div class="container mx-auto px-4">
        <div class="text-center">
          <div class="mb-4">
            <span class="text-pycon-gold text-lg font-semibold">PyCon TW 2025 | Day 1 | R3</span>
          </div>
          <h1 class="hero-title">The Hidden Corners of Python FFI</h1>
          <h2 class="hero-subtitle">Resources & Benchmarks</h2>
          <p class="hero-description mb-4">
            Exploring the complex internals of Python's Foreign Function Interface
          </p>
          <div class="speaker-info">
            <span class="speaker-badge">👤 scc @ CyCraft</span>
            <span class="level-badge">🎯 Advanced</span>
            <span class="lang-badge">🐍 Python Core</span>
          </div>
        </div>
      </div>
    </header>
    
    <main class="container mx-auto px-4 py-12">
      <div class="grid md:grid-cols-2 gap-8">
        <ResourceCard
          title="Source Code"
          description="Benchmark scripts for ctypes, cffi, pybind11, and PyO3. Race condition demos and arena leak examples"
          icon="💻"
          to="/source"
          :file-count="sourceFileCount"
        />
        
        <ResourceCard
          title="Benchmark Data"
          description="Performance metrics, perf profiling data, gdb traces, and glibc arena analysis results"
          icon="📊"
          to="/data"
          :file-count="dataFileCount"
        />
      </div>
      
      <section class="mt-16">
        <h3 class="text-2xl font-bold text-pycon-blue mb-6">Talk Outline</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-12">
          <div class="topic-card">
            <h4 class="topic-title">⚡ FFI Benchmarks</h4>
            <p class="topic-desc">ctypes vs cffi vs pybind11 vs PyO3 performance comparison</p>
          </div>
          <div class="topic-card">
            <h4 class="topic-title">🐢 Free-Threading Impact</h4>
            <p class="topic-desc">Why Free-Threaded Python makes FFI slower</p>
          </div>
          <div class="topic-card">
            <h4 class="topic-title">🏎️ Performance Analysis</h4>
            <p class="topic-desc">Why PyO3 fast but ctypes slow - perf & gdb tracing</p>
          </div>
          <div class="topic-card">
            <h4 class="topic-title">🏁 Racing Conditions</h4>
            <p class="topic-desc">FFI race conditions after No-GIL</p>
          </div>
          <div class="topic-card">
            <h4 class="topic-title">💾 Memory Leaks</h4>
            <p class="topic-desc">Higher risk for Arena leakage in glibc</p>
          </div>
        </div>
      </section>

      <section class="mt-8">
        <h3 class="text-2xl font-bold text-pycon-blue mb-6">Resources</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <a href="https://github.com/scc-tw/pycontw2025" target="_blank" class="quick-link">
            📦 GitHub Repository
          </a>
          <a href="https://tw.pycon.org/2025/en-us/conference/talk/349" target="_blank" class="quick-link">
            🎤 Talk Details on PyCon TW
          </a>
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

.speaker-info {
  @apply flex flex-wrap gap-3 justify-center mt-4;
}

.speaker-badge, .level-badge, .lang-badge {
  @apply inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-white/20 backdrop-blur-sm;
}

.topic-card {
  @apply bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow;
}

.topic-title {
  @apply text-lg font-semibold text-pycon-blue mb-2;
}

.topic-desc {
  @apply text-gray-600;
}
</style>