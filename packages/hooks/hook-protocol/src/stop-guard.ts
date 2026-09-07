/**
 * Consecutive-block accounting for a `Stop` hook point. A blocking Stop hook
 * forces another model step; without a bound an unconditionally blocking hook
 * would continue the same turn forever. The guard counts the blocks one turn
 * has already forced, reports that count as the reference protocols'
 * `stop_hook_active` flag, and refuses the forced continuation once the turn
 * reaches its cap — the same override Claude Code applies after eight
 * consecutive blocks.
 * @module @deepseek-ai/dsh-hook-protocol/stop-guard
 */

/**
 * Claude Code's documented override point: a Stop hook that has blocked eight
 * times in one turn is overridden on the next block. Bridges expose the cap as
 * config and default to this value.
 */
export const DEFAULT_MAX_CONSECUTIVE_STOP_BLOCKS = 8

/** Per-turn Stop block bookkeeping for one bridge. */
export interface StopGuard {
  /**
   * Whether an earlier Stop block already forced this turn to continue — the
   * value the payload's `stop_hook_active` carries so a hook can self-limit.
   * @param agentId - the agent whose turn is at its stop boundary.
   * @param turn - the turn about to close.
   * @returns `true` once the turn has been force-continued at least once.
   */
  active(agentId: string, turn: number): boolean
  /**
   * Record one blocking Stop outcome and decide whether it may force another
   * step. The count is per agent per turn; a new turn starts from zero.
   * @param agentId - the agent whose turn is at its stop boundary.
   * @param turn - the turn about to close.
   * @returns `true` when the block may force continuation; `false` once the
   * turn has already been force-continued `maxConsecutiveBlocks` times.
   */
  block(agentId: string, turn: number): boolean
  /**
   * Drop every record for an agent — call when the agent is disposed so a
   * long-lived bridge does not retain ids of agents that no longer exist.
   * @param agentId - the disposed agent.
   */
  forget(agentId: string): void
}

/**
 * Create a {@link StopGuard} that caps forced continuations per turn.
 * @param maxConsecutiveBlocks - how many times one turn may be force-continued
 *   before a further block is overridden; a positive integer.
 * @returns the guard.
 */
export function createStopGuard(maxConsecutiveBlocks: number): StopGuard {
  if (!Number.isInteger(maxConsecutiveBlocks) || maxConsecutiveBlocks < 1) {
    throw new Error('stop guard: maxConsecutiveBlocks must be a positive integer')
  }
  const records = new Map<string, { turn: number; blocks: number }>()
  function current(agentId: string, turn: number): { turn: number; blocks: number } {
    const record = records.get(agentId)
    if (record !== undefined && record.turn === turn) return record
    const fresh = { turn, blocks: 0 }
    records.set(agentId, fresh)
    return fresh
  }
  return {
    active(agentId, turn) {
      return current(agentId, turn).blocks > 0
    },
    block(agentId, turn) {
      const record = current(agentId, turn)
      if (record.blocks >= maxConsecutiveBlocks) return false
      record.blocks += 1
      return true
    },
    forget(agentId) {
      records.delete(agentId)
    },
  }
}
