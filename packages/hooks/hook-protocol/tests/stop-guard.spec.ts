import { describe, expect, it } from 'vitest'
import { createStopGuard, DEFAULT_MAX_CONSECUTIVE_STOP_BLOCKS } from '@deepseek-ai/dsh-hook-protocol'

describe('createStopGuard', () => {
  it('defaults to the Claude Code override point of eight blocks', () => {
    expect(DEFAULT_MAX_CONSECUTIVE_STOP_BLOCKS).toBe(8)
  })

  it('rejects a non-positive or fractional cap', () => {
    for (const bad of [0, -1, 1.5, Number.NaN]) {
      expect(() => createStopGuard(bad)).toThrow('maxConsecutiveBlocks must be a positive integer')
    }
  })

  it('reports inactive before any block, active after one, and overrides at the cap', () => {
    const guard = createStopGuard(2)
    expect(guard.active('a', 1)).toBe(false)
    expect(guard.block('a', 1)).toBe(true)
    expect(guard.active('a', 1)).toBe(true)
    expect(guard.block('a', 1)).toBe(true)
    // Cap reached: a further block is refused and the count does not grow.
    expect(guard.block('a', 1)).toBe(false)
    expect(guard.block('a', 1)).toBe(false)
    expect(guard.active('a', 1)).toBe(true)
  })

  it('keeps counts per agent and per turn', () => {
    const guard = createStopGuard(1)
    expect(guard.block('a', 1)).toBe(true)
    expect(guard.block('a', 1)).toBe(false)
    // Another agent's same turn number is independent.
    expect(guard.active('b', 1)).toBe(false)
    expect(guard.block('b', 1)).toBe(true)
    // A new turn on the first agent starts from zero.
    expect(guard.active('a', 2)).toBe(false)
    expect(guard.block('a', 2)).toBe(true)
    // The earlier turn's record is gone once a later turn replaces it.
    expect(guard.active('a', 1)).toBe(false)
  })

  it('forget drops an agent record', () => {
    const guard = createStopGuard(1)
    expect(guard.block('a', 1)).toBe(true)
    guard.forget('a')
    expect(guard.active('a', 1)).toBe(false)
    expect(guard.block('a', 1)).toBe(true)
  })
})
