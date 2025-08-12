/**
 * Performance statistics interface
 */
export interface PerformanceStats {
  count: number
  average: number
  min: number
  max: number
  median: number
}

/**
 * Performance metrics interface
 */
export interface PerformanceMetric {
  name: string
  value: number
  unit: 'ms' | 'bytes' | 'count'
  timestamp: number
  metadata?: Record<string, unknown>
}

/**
 * Performance Service for monitoring application performance
 */
export interface IPerformanceService {
  startTimer(label: string): void
  endTimer(label: string): number
  measureAsync<T>(label: string, fn: () => Promise<T>): Promise<T>
  recordMetric(name: string, value: number, unit: 'ms' | 'bytes' | 'count'): void
  getMetrics(): PerformanceMetric[]
  clearMetrics(): void
  getAverageMetric(name: string): number | null
}

export class PerformanceService implements IPerformanceService {
  private timers: Map<string, number> = new Map()
  private metrics: PerformanceMetric[] = []
  private readonly maxMetricsSize = 1000

  /**
   * Start a performance timer
   */
  startTimer(label: string): void {
    this.timers.set(label, performance.now())
  }

  /**
   * End a timer and record the duration
   */
  endTimer(label: string): number {
    const startTime = this.timers.get(label)
    if (!startTime) {
      console.warn(`Timer '${label}' was not started`)
      return 0
    }
    
    const duration = performance.now() - startTime
    this.timers.delete(label)
    
    this.recordMetric(label, duration, 'ms')
    return duration
  }

  /**
   * Measure async function execution time
   */
  async measureAsync<T>(label: string, fn: () => Promise<T>): Promise<T> {
    this.startTimer(label)
    try {
      const result = await fn()
      this.endTimer(label)
      return result
    } catch (error) {
      this.endTimer(label)
      throw error
    }
  }

  /**
   * Record a performance metric
   */
  recordMetric(
    name: string,
    value: number,
    unit: 'ms' | 'bytes' | 'count' = 'ms',
    metadata?: Record<string, unknown>
  ): void {
    const metric: PerformanceMetric = {
      name,
      value,
      unit,
      timestamp: Date.now(),
      metadata
    }
    
    this.metrics.push(metric)
    
    // Maintain metrics size limit
    if (this.metrics.length > this.maxMetricsSize) {
      this.metrics.shift()
    }
    
    // Log slow operations in development
    if (import.meta.env.DEV && unit === 'ms' && value > 1000) {
      console.warn(`Slow operation detected: ${name} took ${value.toFixed(2)}ms`)
    }
  }

  /**
   * Get all recorded metrics
   */
  getMetrics(): PerformanceMetric[] {
    return [...this.metrics]
  }

  /**
   * Clear all metrics
   */
  clearMetrics(): void {
    this.metrics = []
    this.timers.clear()
  }

  /**
   * Get average value for a specific metric
   */
  getAverageMetric(name: string): number | null {
    const relevantMetrics = this.metrics.filter(m => m.name === name)
    
    if (relevantMetrics.length === 0) {
      return null
    }
    
    const sum = relevantMetrics.reduce((acc, m) => acc + m.value, 0)
    return sum / relevantMetrics.length
  }

  /**
   * Get performance report
   */
  getReport(): Record<string, PerformanceStats> {
    const report: Record<string, PerformanceStats> = {}
    
    // Group metrics by name
    const grouped = this.metrics.reduce((acc, metric) => {
      if (!acc[metric.name]) {
        acc[metric.name] = []
      }
      acc[metric.name].push(metric.value)
      return acc
    }, {} as Record<string, number[]>)
    
    // Calculate statistics for each metric
    Object.entries(grouped).forEach(([name, values]) => {
      report[name] = {
        count: values.length,
        average: values.reduce((a, b) => a + b, 0) / values.length,
        min: Math.min(...values),
        max: Math.max(...values),
        median: this.calculateMedian(values)
      }
    })
    
    return report
  }

  /**
   * Calculate median value
   */
  private calculateMedian(values: number[]): number {
    const sorted = [...values].sort((a, b) => a - b)
    const mid = Math.floor(sorted.length / 2)
    
    if (sorted.length % 2 === 0) {
      return (sorted[mid - 1] + sorted[mid]) / 2
    }
    
    return sorted[mid]
  }
}