import { ref, onMounted, onUnmounted } from 'vue'

/**
 * Composable for accessibility features
 * Implements keyboard navigation and ARIA support
 */
export function useAccessibility() {
  const isKeyboardUser = ref(false)
  const announcements = ref<string[]>([])
  
  /**
   * Detect keyboard vs mouse user
   */
  const detectInputMethod = (e: KeyboardEvent | MouseEvent) => {
    if (e.type === 'keydown' && (e as KeyboardEvent).key === 'Tab') {
      isKeyboardUser.value = true
      document.body.classList.add('keyboard-user')
    } else if (e.type === 'mousedown') {
      isKeyboardUser.value = false
      document.body.classList.remove('keyboard-user')
    }
  }
  
  /**
   * Announce message to screen readers
   */
  const announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    announcements.value.push(message)
    
    // Create or update live region
    let liveRegion = document.getElementById('aria-live-region')
    if (!liveRegion) {
      liveRegion = document.createElement('div')
      liveRegion.id = 'aria-live-region'
      liveRegion.setAttribute('aria-live', priority)
      liveRegion.setAttribute('aria-atomic', 'true')
      liveRegion.classList.add('sr-only')
      document.body.appendChild(liveRegion)
    }
    
    liveRegion.textContent = message
    
    // Clear after announcement
    setTimeout(() => {
      if (liveRegion) {
        liveRegion.textContent = ''
      }
    }, 1000)
  }
  
  /**
   * Trap focus within an element
   */
  const trapFocus = (element: HTMLElement) => {
    const focusableElements = element.querySelectorAll(
      'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select, [tabindex]:not([tabindex="-1"])'
    )
    
    const firstFocusable = focusableElements[0] as HTMLElement
    const lastFocusable = focusableElements[focusableElements.length - 1] as HTMLElement
    
    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return
      
      if (e.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstFocusable) {
          e.preventDefault()
          lastFocusable?.focus()
        }
      } else {
        // Tab
        if (document.activeElement === lastFocusable) {
          e.preventDefault()
          firstFocusable?.focus()
        }
      }
    }
    
    element.addEventListener('keydown', handleTabKey)
    
    return () => {
      element.removeEventListener('keydown', handleTabKey)
    }
  }
  
  /**
   * Handle escape key
   */
  const onEscape = (callback: () => void) => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        callback()
      }
    }
    
    document.addEventListener('keydown', handleEscape)
    
    return () => {
      document.removeEventListener('keydown', handleEscape)
    }
  }
  
  /**
   * Setup accessibility listeners
   */
  onMounted(() => {
    document.addEventListener('keydown', detectInputMethod)
    document.addEventListener('mousedown', detectInputMethod)
  })
  
  onUnmounted(() => {
    document.removeEventListener('keydown', detectInputMethod)
    document.removeEventListener('mousedown', detectInputMethod)
  })
  
  return {
    isKeyboardUser,
    announcements,
    announce,
    trapFocus,
    onEscape
  }
}

/**
 * Keyboard navigation composable
 */
export function useKeyboardNavigation() {
  const currentIndex = ref(0)
  
  /**
   * Navigate through items with arrow keys
   */
  const handleArrowNavigation = (
    e: KeyboardEvent,
    items: HTMLElement[],
    orientation: 'horizontal' | 'vertical' = 'vertical'
  ) => {
    const key = e.key
    let newIndex = currentIndex.value
    
    if (orientation === 'vertical') {
      if (key === 'ArrowUp') {
        e.preventDefault()
        newIndex = Math.max(0, currentIndex.value - 1)
      } else if (key === 'ArrowDown') {
        e.preventDefault()
        newIndex = Math.min(items.length - 1, currentIndex.value + 1)
      }
    } else {
      if (key === 'ArrowLeft') {
        e.preventDefault()
        newIndex = Math.max(0, currentIndex.value - 1)
      } else if (key === 'ArrowRight') {
        e.preventDefault()
        newIndex = Math.min(items.length - 1, currentIndex.value + 1)
      }
    }
    
    if (key === 'Home') {
      e.preventDefault()
      newIndex = 0
    } else if (key === 'End') {
      e.preventDefault()
      newIndex = items.length - 1
    }
    
    if (newIndex !== currentIndex.value) {
      currentIndex.value = newIndex
      items[newIndex]?.focus()
    }
  }
  
  return {
    currentIndex,
    handleArrowNavigation
  }
}