import { describe, it, expect } from 'vitest'
import { nanoid } from './nanoid'

describe('nanoid', () => {
  it('generates an ID with default length of 21', () => {
    const id = nanoid()
    expect(id).toHaveLength(21)
  })

  it('generates an ID with custom length', () => {
    expect(nanoid(10)).toHaveLength(10)
    expect(nanoid(5)).toHaveLength(5)
    expect(nanoid(50)).toHaveLength(50)
  })

  it('generates unique IDs', () => {
    const ids = new Set<string>()
    for (let i = 0; i < 1000; i++) {
      ids.add(nanoid())
    }
    // All 1000 IDs should be unique
    expect(ids.size).toBe(1000)
  })

  it('only uses alphanumeric characters', () => {
    const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    for (let i = 0; i < 100; i++) {
      const id = nanoid()
      for (const char of id) {
        expect(alphabet).toContain(char)
      }
    }
  })

  it('handles size of 1', () => {
    const id = nanoid(1)
    expect(id).toHaveLength(1)
  })

  it('handles size of 0', () => {
    const id = nanoid(0)
    expect(id).toHaveLength(0)
    expect(id).toBe('')
  })
})
