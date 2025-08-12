import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { ServiceContainer } from './services/ServiceContainer'
import type { IErrorService } from './services/ErrorService'

// Initialize services
ServiceContainer.getInstance()

const app = createApp(App)

app.use(router)

// Global error handler
app.config.errorHandler = (err, _instance, info) => {
  const container = ServiceContainer.getInstance()
  const errorService = container.get<IErrorService>('ErrorService')
  if (errorService && typeof errorService.handleError === 'function') {
    errorService.handleError(err as Error)
  }
  console.error('Global error:', err, info)
}

app.mount('#app')