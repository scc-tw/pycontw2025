<template>
  <Transition name="modal">
    <div v-if="visible" class="modal-overlay" @click="handleOverlayClick">
      <div class="modal-container" @click.stop>
        <div class="modal-header">
          <h2 class="modal-title">📜 GPL License Agreement</h2>
          <button @click="close" class="modal-close" aria-label="Close">
            ✕
          </button>
        </div>
        
        <div class="modal-body">
          <div class="license-notice">
            <p class="notice-text">
              The presentation slides and associated materials are licensed under the 
              <strong>GNU General Public License v3.0 (GPL-3.0)</strong>.
            </p>
          </div>
          
          <div class="license-content">
            <h3>Key Terms:</h3>
            <ul class="license-terms">
              <li>✅ You are free to use, modify, and distribute these materials</li>
              <li>✅ Any derivative work must also be licensed under GPL-3.0</li>
              <li>✅ You must include the original copyright notice</li>
              <li>✅ Source code/materials must be made available</li>
              <li>⚠️ No warranty is provided with these materials</li>
            </ul>
            
            <div class="license-text">
              <h4>GNU GENERAL PUBLIC LICENSE</h4>
              <p>Version 3, 29 June 2007</p>
              <p class="copyright">
                Copyright © 2025 scc @ CyCraft<br>
                PyCon TW 2025 - The Hidden Corners of Python FFI
              </p>
              <p class="license-summary">
                This program is free software: you can redistribute it and/or modify
                it under the terms of the GNU General Public License as published by
                the Free Software Foundation, either version 3 of the License, or
                (at your option) any later version.
              </p>
              <p class="license-summary">
                This program is distributed in the hope that it will be useful,
                but WITHOUT ANY WARRANTY; without even the implied warranty of
                MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
                GNU General Public License for more details.
              </p>
              <p class="license-link">
                <a href="https://www.gnu.org/licenses/gpl-3.0.html" target="_blank" class="gpl-link">
                  📖 Read Full GPL-3.0 License
                </a>
              </p>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="decline" class="btn-decline">
            Decline
          </button>
          <button @click="accept" class="btn-accept">
            I Accept the GPL License
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'accept'): void
  (e: 'decline'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = ref(props.modelValue)

const close = () => {
  visible.value = false
  emit('update:modelValue', false)
}

const accept = () => {
  emit('accept')
  close()
}

const decline = () => {
  emit('decline')
  close()
}

const handleOverlayClick = (e: MouseEvent) => {
  // Close on overlay click
  if (e.target === e.currentTarget) {
    decline()
  }
}

// Watch for external changes
import { watch } from 'vue'
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})
</script>

<style scoped>
.modal-overlay {
  @apply fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4;
}

.modal-container {
  @apply bg-white rounded-lg shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col;
}

.modal-header {
  @apply flex items-center justify-between p-6 border-b border-gray-200;
}

.modal-title {
  @apply text-2xl font-bold text-gray-900;
}

.modal-close {
  @apply text-gray-400 hover:text-gray-600 text-2xl font-bold leading-none transition-colors;
}

.modal-body {
  @apply p-6 overflow-y-auto flex-1;
}

.license-notice {
  @apply bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6;
}

.notice-text {
  @apply text-blue-900 mb-0;
}

.license-content {
  @apply space-y-4;
}

.license-content h3 {
  @apply text-lg font-semibold text-gray-900 mb-3;
}

.license-terms {
  @apply space-y-2 mb-6;
}

.license-terms li {
  @apply flex items-start text-gray-700;
}

.license-text {
  @apply bg-gray-50 rounded-lg p-4 space-y-3;
}

.license-text h4 {
  @apply font-bold text-gray-900 mb-1;
}

.copyright {
  @apply text-sm text-gray-600 italic;
}

.license-summary {
  @apply text-sm text-gray-700 leading-relaxed;
}

.license-link {
  @apply mt-4 pt-4 border-t border-gray-200;
}

.gpl-link {
  @apply text-blue-600 hover:text-blue-800 font-semibold inline-flex items-center gap-1 transition-colors;
}

.modal-footer {
  @apply flex justify-end gap-3 p-6 border-t border-gray-200;
}

.btn-decline {
  @apply px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors font-medium;
}

.btn-accept {
  @apply px-6 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors font-medium;
}

/* Transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.3s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.9);
}
</style>