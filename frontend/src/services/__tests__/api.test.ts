import { describe, it, expect, vi, beforeEach } from 'vitest'
import api, {
  fetchDocuments,
  fetchStats,
  uploadDocument,
  deleteDocument,
  queryChat,
} from '../api'

// Mock axios
vi.mock('axios')

const mockedApi = {
  get: vi.fn(),
  post: vi.fn(),
  delete: vi.fn(),
}

api.get = mockedApi.get
api.post = mockedApi.post
api.delete = mockedApi.delete

describe('API Services', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchDocuments', () => {
    it('should fetch documents successfully', async () => {
      const mockResponse = {
        data: {
          documents: [
            { id: '1', title: 'Test Doc', doc_type: 'pdf', status: 'completed' },
          ],
          total: 1,
        },
      }
      mockedApi.get.mockResolvedValueOnce(mockResponse)

      const result = await fetchDocuments()

      expect(mockedApi.get).toHaveBeenCalledWith('/api/documents/')
      expect(result).toEqual(mockResponse.data)
    })

    it('should throw error on failed fetch', async () => {
      mockedApi.get.mockRejectedValueOnce(new Error('Network error'))

      await expect(fetchDocuments()).rejects.toThrow('Network error')
    })
  })

  describe('fetchStats', () => {
    it('should fetch stats successfully', async () => {
      const mockResponse = {
        data: {
          documents: { total: 10 },
          chunks: { total: 50 },
        },
      }
      mockedApi.get.mockResolvedValueOnce(mockResponse)

      const result = await fetchStats()

      expect(mockedApi.get).toHaveBeenCalledWith('/api/stats')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('uploadDocument', () => {
    it('should upload document successfully', async () => {
      const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' })
      const mockResponse = {
        data: { id: '1', title: 'test', status: 'completed' },
      }
      mockedApi.post.mockResolvedValueOnce(mockResponse)

      const result = await uploadDocument(mockFile)

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/api/documents/',
        expect.any(FormData),
        {
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      )
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('deleteDocument', () => {
    it('should delete document successfully', async () => {
      mockedApi.delete.mockResolvedValueOnce({})

      await deleteDocument('doc-1')

      expect(mockedApi.delete).toHaveBeenCalledWith('/api/documents/doc-1')
    })
  })

  describe('queryChat', () => {
    it('should send chat message successfully', async () => {
      const mockResponse = {
        data: {
          message: 'Test response',
          sources: [],
        },
      }
      mockedApi.post.mockResolvedValueOnce(mockResponse)

      const result = await queryChat('Hello', [])

      expect(mockedApi.post).toHaveBeenCalledWith('/api/chat', {
        message: 'Hello',
        history: [],
      })
      expect(result).toEqual(mockResponse.data)
    })
  })
})
