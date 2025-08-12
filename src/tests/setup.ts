import { config } from '@vue/test-utils'
import { vi } from 'vitest'

// Mock fetch globally
global.fetch = vi.fn()

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:3000',
    reload: vi.fn()
  },
  writable: true
})

// Setup Vue Test Utils global config
config.global.mocks = {
  $t: (key: string) => key // Mock i18n if needed
}