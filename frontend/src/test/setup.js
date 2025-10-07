/**
 * Test Setup File
 *
 * This file runs before all tests to configure the testing environment.
 * It extends Vitest with React Testing Library matchers.
 */

import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom'

// Cleanup after each test (unmount React components)
// This ensures tests don't affect each other
afterEach(() => {
  cleanup()
})
