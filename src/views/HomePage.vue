<template>
  <div class="home-page">
    <header class="hero-section">
      <div class="container mx-auto px-4">
        <div class="text-center max-w-3xl mx-auto">
          <div class="mb-3">
            <span class="text-label uppercase text-theme-muted">PyCon TW 2025 | Day 1 | R3</span>
          </div>
          <h1 class="hero-title">The Hidden Corners of Python FFI</h1>
          <h2 class="hero-subtitle">Resources & Benchmarks</h2>
          <p class="hero-description prose mb-4">
            Exploring the complex internals of Python's Foreign Function Interface
          </p>
          <div class="speaker-info">
            <span class="tag">👤 scc @ CyCraft</span>
            <span class="tag">🎯 Advanced</span>
            <span class="tag">🐍 Python Core</span>
          </div>
        </div>
      </div>
    </header>
    
    <main class="container mx-auto px-4 py-12">
      <div class="grid md:grid-cols-2 gap-gap-md">
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
        <h3 class="text-headline text-theme-ink mb-6">Talk Outline</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gap-sm mb-12">
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
        <h3 class="text-headline text-theme-ink mb-6">Resources</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-gap-sm">
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
  @apply min-h-screen bg-theme-bg;
}

.hero-section {
  @apply bg-theme-surface text-theme-ink py-16 border-b border-theme-border;
}

.hero-title {
  @apply text-display mb-2;
}

.hero-subtitle {
  @apply text-headline mb-4 text-theme-accent;
}

.hero-description {
  @apply text-body text-theme-ink max-w-readable mx-auto leading-relaxed;
}

.quick-link {
  @apply flex items-center justify-center p-4 bg-theme-surface rounded-sm border border-theme-border hover:bg-theme-hover-surface transition-all text-theme-accent font-semibold min-h-[44px];
}

.speaker-info {
  @apply flex flex-wrap gap-gap-sm justify-center mt-4;
}

.topic-card {
  @apply bg-theme-surface p-4 rounded-sm border border-theme-border hover:bg-theme-hover-surface transition-all;
}

.topic-title {
  @apply text-title text-theme-ink mb-2;
}

.topic-desc {
  @apply text-body text-theme-muted;
}
</style>