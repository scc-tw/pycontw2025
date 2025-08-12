<template>
  <div id="app">
    <nav class="app-navbar">
      <div class="container mx-auto px-4">
        <div class="flex items-center justify-between h-16">
          <router-link to="/" class="brand">
            🐍 PyCon TW 2025 Resources
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
      <div class="container mx-auto px-4 py-6 text-center text-sm text-gray-600">
        <p>© 2025 PyCon Taiwan. Built with Vue 3 + Vite + TypeScript by Claude & SCC</p>
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
  @apply bg-pycon-blue text-white shadow-lg sticky top-0 z-50;
}

.brand {
  @apply text-xl font-bold hover:text-pycon-gold transition-colors;
}

.nav-links {
  @apply flex space-x-6;
}

.nav-link {
  @apply hover:text-pycon-gold transition-colors;
}

.nav-link.router-link-active {
  @apply text-pycon-gold font-semibold;
}

.app-footer {
  @apply bg-gray-100 border-t border-gray-200 mt-auto;
}

.footer-link {
  @apply text-pycon-blue hover:underline;
}
</style>