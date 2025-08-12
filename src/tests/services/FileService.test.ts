import { describe, it, expect, beforeEach, vi } from 'vitest'
import { FileService } from '@/services/FileService'

describe('FileService', () => {
  let fileService: FileService
  
  beforeEach(() => {
    fileService = new FileService('/', 'test-repo', 'main')
    vi.clearAllMocks()
  })
  
  describe('fetchFileTree', () => {
    it('should fetch and transform file tree from manifest', async () => {
      const mockManifest = {
        files: [
          'resources/source/test.py',
          'resources/source/utils/helper.py'
        ]
      }
      
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockManifest
      } as Response)
      
      const result = await fileService.fetchFileTree('resources/source')
      
      expect(result).toHaveLength(2)
      expect(result[0]).toMatchObject({
        name: 'test.py',
        type: 'file',
        language: 'python'
      })
    })
    
    it('should use cache on subsequent calls', async () => {
      const mockManifest = { files: ['test.txt'] }
      
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockManifest
      } as Response)
      
      // First call
      await fileService.fetchFileTree('resources')
      // Second call should use cache
      await fileService.fetchFileTree('resources')
      
      expect(global.fetch).toHaveBeenCalledTimes(1)
    })
    
    it('should handle fetch errors gracefully', async () => {
      global.fetch = vi.fn().mockRejectedValueOnce(new Error('Network error'))
      
      const result = await fileService.fetchFileTree('resources')
      
      // Should return mock data on error
      expect(result).toEqual([])
    })
  })
  
  describe('fetchFileContent', () => {
    it('should fetch file content successfully', async () => {
      const mockContent = 'print("Hello, PyCon!")'
      
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        text: async () => mockContent
      } as Response)
      
      const content = await fileService.fetchFileContent('/test.py')
      
      expect(content).toBe(mockContent)
      expect(global.fetch).toHaveBeenCalledWith('/test.py')
    })
    
    it('should throw error on failed fetch', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        statusText: 'Not Found'
      } as Response)
      
      await expect(fileService.fetchFileContent('/missing.txt'))
        .rejects.toThrow('Failed to fetch file: Not Found')
    })
    
    it('should sanitize file paths', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        text: async () => 'content'
      } as Response)
      
      await fileService.fetchFileContent('/../../../etc/passwd')
      
      // Path should be sanitized
      expect(global.fetch).toHaveBeenCalledWith('/etc/passwd')
    })
  })
  
  describe('getDownloadUrl', () => {
    it('should generate correct download URL', () => {
      const url = fileService.getDownloadUrl('/resources/test.pdf')
      expect(url).toBe('/resources/test.pdf')
    })
    
    it('should sanitize paths in download URL', () => {
      const url = fileService.getDownloadUrl('/../test.pdf')
      expect(url).toBe('/test.pdf')
    })
  })
  
  describe('getRawGitHubUrl', () => {
    it('should generate correct GitHub raw URL', () => {
      const url = fileService.getRawGitHubUrl('/resources/test.py')
      expect(url).toBe('https://raw.githubusercontent.com/test-repo/main/resources/test.py')
    })
  })
})