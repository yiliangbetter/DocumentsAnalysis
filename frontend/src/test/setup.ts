// Test setup file for Vitest
import '@testing-library/jest-dom'

// Clean up after each test
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

// Mock fetch globally
globalThis.fetch = vi.fn()

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})
