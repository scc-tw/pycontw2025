<template>
  <div id="app">
    <nav class="app-navbar">
      <div class="container mx-auto px-4">
        <div class="flex items-center justify-between h-16">
          <router-link to="/" class="brand">
            🐍 PyCon TW 2025 FFI
          </router-link>
          
          <div class="nav-links">
            <router-link to="/source" class="nav-link">
              Source Code
            </router-link>
            <router-link to="/data" class="nav-link">
              Benchmark Data
            </router-link>
          </div>
        </div>
      </div>
    </nav>
    
    <router-view />
    
    <footer class="app-footer">
      <div class="container mx-auto px-4 py-6 text-center text-label text-theme-muted">
        <p>© 2025 scc @ CyCraft | PyCon Taiwan 2025 Talk Resources</p>
        <p class="mt-2">
          <a href="https://github.com/scc-tw/pycontw2025" target="_blank" class="footer-link">
            GitHub
          </a>
          <span class="mx-2">•</span>
          <a href="https://tw.pycon.org" target="_blank" class="footer-link">
            PyCon TW
          </a>
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
// App setup logic if needed
</script>

<style>
@import './assets/main.css';

.app-navbar {
  @apply bg-theme-surface text-theme-ink border-b border-theme-border shadow-card sticky top-0 z-50;
}

.brand {
  @apply text-title font-semibold hover:text-theme-accent transition-colors;
}

.nav-links {
  @apply flex items-center gap-gap-lg;
}

.nav-link {
  @apply text-body hover:text-theme-accent transition-all duration-[160ms] px-2 py-1 rounded-sm;
}

.nav-link.router-link-active {
  @apply text-theme-accent font-semibold border-b-2 border-theme-accent;
}

.app-footer {
  @apply bg-theme-ui border-t border-theme-border mt-auto;
}

.footer-link {
  @apply text-theme-accent hover:underline transition-all duration-[160ms];
}
</style>