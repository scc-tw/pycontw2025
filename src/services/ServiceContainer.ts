import { FileService, type IFileService } from './FileService'
import { NavigationService, type INavigationService } from './NavigationService'
import { ConfigService, type IConfigService } from './ConfigService'
import { ErrorService, type IErrorService } from './ErrorService'
import { PerformanceService, type IPerformanceService } from './PerformanceService'

/**
 * Service Container for Dependency Injection
 * Implements Inversion of Control (IoC) pattern
 */
export class ServiceContainer {
  private static instance: ServiceContainer
  private services: Map<string, unknown> = new Map()

  private constructor() {
    this.registerServices()
  }

  /**
   * Singleton pattern to ensure single instance
   */
  static getInstance(): ServiceContainer {
    if (!ServiceContainer.instance) {
      ServiceContainer.instance = new ServiceContainer()
    }
    return ServiceContainer.instance
  }

  /**
   * Register all services
   */
  private registerServices(): void {
    // Register ConfigService first as other services may depend on it
    const configService = new ConfigService()
    this.services.set('ConfigService', configService)

    // Register ErrorService
    const errorService = new ErrorService()
    this.services.set('ErrorService', errorService)

    // Register PerformanceService
    const performanceService = new PerformanceService()
    this.services.set('PerformanceService', performanceService)

    // Register FileService
    const fileService = new FileService(
      configService.get<string>('BASE_URL'),
      configService.get<string>('GITHUB_REPO'),
      configService.get<string>('GITHUB_BRANCH')
    )
    this.services.set('FileService', fileService)

    // Register NavigationService
    const navigationService = new NavigationService()
    this.services.set('NavigationService', navigationService)
  }

  /**
   * Get service by name with type safety
   */
  get<T>(serviceName: string): T {
    const service = this.services.get(serviceName)
    if (!service) {
      throw new Error(`Service ${serviceName} not found in container`)
    }
    return service as T
  }

  /**
   * Type-safe service getters
   */
  getFileService(): IFileService {
    return this.get<IFileService>('FileService')
  }

  getNavigationService(): INavigationService {
    return this.get<INavigationService>('NavigationService')
  }

  getConfigService(): IConfigService {
    return this.get<IConfigService>('ConfigService')
  }

  getErrorService(): IErrorService {
    return this.get<IErrorService>('ErrorService')
  }

  getPerformanceService(): IPerformanceService {
    return this.get<IPerformanceService>('PerformanceService')
  }

  /**
   * Clear all services (useful for testing)
   */
  clear(): void {
    this.services.clear()
    ServiceContainer.instance = null as unknown as ServiceContainer
  }
}