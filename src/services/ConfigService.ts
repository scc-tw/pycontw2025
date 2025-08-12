/**
 * Configuration Service for managing application settings
 * Implements environment-based configuration
 */
export interface IConfigService {
  get<T = unknown>(key: string): T
  set<T = unknown>(key: string, value: T): void
  getAll(): Record<string, unknown>
  isProduction(): boolean
  isDevelopment(): boolean
}

export class ConfigService implements IConfigService {
  private config: Record<string, unknown>

  constructor() {
    this.config = this.loadConfiguration()
  }

  /**
   * Load configuration based on environment
   */
  private loadConfiguration(): Record<string, unknown> {
    const env = import.meta.env
    
    return {
      // Application settings
      APP_NAME: 'PyCon TW 2025 Resources',
      APP_VERSION: '1.0.0',
      
      // URLs and paths
      BASE_URL: env.BASE_URL || '/',
      API_URL: env.VITE_API_URL || '/api',
      
      // GitHub settings
      GITHUB_REPO: 'scc-tw/pycontw2025',
      GITHUB_BRANCH: 'gh-pages',
      GITHUB_OWNER: 'scc-tw',
      
      // Feature flags
      ENABLE_CACHE: env.VITE_ENABLE_CACHE !== 'false',
      ENABLE_MOCK_DATA: env.DEV || false,
      ENABLE_ANALYTICS: env.VITE_ENABLE_ANALYTICS === 'true',
      
      // Performance settings
      CACHE_TTL: 5 * 60 * 1000, // 5 minutes
      MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
      DEBOUNCE_DELAY: 300, // milliseconds
      
      // UI settings
      ITEMS_PER_PAGE: 50,
      MAX_BREADCRUMB_ITEMS: 5,
      THEME: env.VITE_THEME || 'default',
      
      // Environment
      NODE_ENV: env.MODE,
      IS_PRODUCTION: env.PROD,
      IS_DEVELOPMENT: env.DEV
    }
  }

  /**
   * Get configuration value by key
   */
  get<T = unknown>(key: string): T {
    return this.config[key] as T
  }

  /**
   * Set configuration value
   */
  set<T = unknown>(key: string, value: T): void {
    this.config[key] = value
  }

  /**
   * Get all configuration values
   */
  getAll(): Record<string, unknown> {
    return { ...this.config }
  }

  /**
   * Check if running in production
   */
  isProduction(): boolean {
    return this.config.IS_PRODUCTION === true
  }

  /**
   * Check if running in development
   */
  isDevelopment(): boolean {
    return this.config.IS_DEVELOPMENT === true
  }
}