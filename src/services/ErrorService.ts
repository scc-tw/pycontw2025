/**
 * Error types for categorizing errors
 */
export enum ErrorType {
  NETWORK = 'NETWORK',
  FILE_NOT_FOUND = 'FILE_NOT_FOUND',
  INVALID_FORMAT = 'INVALID_FORMAT',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  VALIDATION = 'VALIDATION',
  UNKNOWN = 'UNKNOWN'
}

/**
 * Error severity levels
 */
export enum ErrorSeverity {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

/**
 * Application error class with additional metadata
 */
export class AppError extends Error {
  public readonly type: ErrorType
  public readonly severity: ErrorSeverity
  public readonly timestamp: Date
  public readonly context?: Record<string, unknown>
  public readonly recoverable: boolean

  constructor(
    message: string,
    type: ErrorType = ErrorType.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    recoverable: boolean = true,
    context?: Record<string, unknown>
  ) {
    super(message)
    this.name = 'AppError'
    this.type = type
    this.severity = severity
    this.timestamp = new Date()
    this.context = context
    this.recoverable = recoverable
    
    // Maintains proper stack trace for where error was thrown
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, AppError)
    }
  }
}

/**
 * Error handler callback type
 */
type ErrorHandler = (error: AppError) => void

/**
 * Error Service for centralized error handling
 */
export interface IErrorService {
  handleError(error: Error | AppError): void
  createError(message: string, type?: ErrorType, severity?: ErrorSeverity): AppError
  onError(handler: ErrorHandler): void
  clearHandlers(): void
  getErrorLog(): AppError[]
}

export class ErrorService implements IErrorService {
  private errorHandlers: Set<ErrorHandler> = new Set()
  private errorLog: AppError[] = []
  private readonly maxLogSize = 100

  /**
   * Handle an error with proper logging and notification
   */
  handleError(error: Error | AppError): void {
    let appError: AppError
    
    if (error instanceof AppError) {
      appError = error
    } else {
      // Convert regular errors to AppError
      appError = this.convertToAppError(error)
    }
    
    // Log the error
    this.logError(appError)
    
    // Notify all registered handlers
    this.notifyHandlers(appError)
    
    // Console output in development
    if (import.meta.env.DEV) {
      console.error('[ErrorService]', appError)
    }
    
    // Handle critical errors
    if (appError.severity === ErrorSeverity.CRITICAL && !appError.recoverable) {
      this.handleCriticalError(appError)
    }
  }

  /**
   * Create a new AppError
   */
  createError(
    message: string,
    type: ErrorType = ErrorType.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
  ): AppError {
    return new AppError(message, type, severity)
  }

  /**
   * Register an error handler
   */
  onError(handler: ErrorHandler): void {
    this.errorHandlers.add(handler)
  }

  /**
   * Clear all error handlers
   */
  clearHandlers(): void {
    this.errorHandlers.clear()
  }

  /**
   * Get error log
   */
  getErrorLog(): AppError[] {
    return [...this.errorLog]
  }

  /**
   * Convert regular Error to AppError
   */
  private convertToAppError(error: Error): AppError {
    // Detect error type based on error message or properties
    let type = ErrorType.UNKNOWN
    let severity = ErrorSeverity.MEDIUM
    
    if (error.message.includes('fetch') || error.message.includes('network')) {
      type = ErrorType.NETWORK
    } else if (error.message.includes('404') || error.message.includes('not found')) {
      type = ErrorType.FILE_NOT_FOUND
      severity = ErrorSeverity.LOW
    } else if (error.message.includes('permission') || error.message.includes('denied')) {
      type = ErrorType.PERMISSION_DENIED
      severity = ErrorSeverity.HIGH
    }
    
    return new AppError(
      error.message,
      type,
      severity,
      true,
      { originalError: error.name, stack: error.stack }
    )
  }

  /**
   * Log error to internal log
   */
  private logError(error: AppError): void {
    this.errorLog.push(error)
    
    // Maintain log size limit
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog.shift()
    }
  }

  /**
   * Notify all registered error handlers
   */
  private notifyHandlers(error: AppError): void {
    this.errorHandlers.forEach(handler => {
      try {
        handler(error)
      } catch (handlerError) {
        console.error('Error in error handler:', handlerError)
      }
    })
  }

  /**
   * Handle critical errors that can't be recovered
   */
  private handleCriticalError(error: AppError): void {
    // In a real application, this might:
    // - Send error to monitoring service
    // - Show a fallback UI
    // - Attempt to save user data
    console.error('CRITICAL ERROR:', error)
    
    // Optionally reload the page after a delay
    if (import.meta.env.PROD) {
      setTimeout(() => {
        window.location.reload()
      }, 5000)
    }
  }
}