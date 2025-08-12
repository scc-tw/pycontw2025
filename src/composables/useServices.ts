import { ServiceContainer } from '@/services/ServiceContainer'
import type { IFileService } from '@/services/FileService'
import type { INavigationService } from '@/services/NavigationService'
import type { IConfigService } from '@/services/ConfigService'
import type { IErrorService } from '@/services/ErrorService'
import type { IPerformanceService } from '@/services/PerformanceService'

/**
 * Composable for accessing services through dependency injection
 * Provides type-safe access to all application services
 */
export function useServices() {
  const container = ServiceContainer.getInstance()
  
  return {
    fileService: container.getFileService(),
    navigationService: container.getNavigationService(),
    configService: container.getConfigService(),
    errorService: container.get<IErrorService>('ErrorService'),
    performanceService: container.get<IPerformanceService>('PerformanceService'),
    container
  }
}

/**
 * Composable for file operations
 */
export function useFileService(): IFileService {
  const container = ServiceContainer.getInstance()
  return container.getFileService()
}

/**
 * Composable for navigation
 */
export function useNavigationService(): INavigationService {
  const container = ServiceContainer.getInstance()
  return container.getNavigationService()
}

/**
 * Composable for configuration
 */
export function useConfigService(): IConfigService {
  const container = ServiceContainer.getInstance()
  return container.getConfigService()
}

/**
 * Composable for error handling
 */
export function useErrorService(): IErrorService {
  const container = ServiceContainer.getInstance()
  return container.get<IErrorService>('ErrorService')
}

/**
 * Composable for performance monitoring
 */
export function usePerformanceService(): IPerformanceService {
  const container = ServiceContainer.getInstance()
  return container.get<IPerformanceService>('PerformanceService')
}