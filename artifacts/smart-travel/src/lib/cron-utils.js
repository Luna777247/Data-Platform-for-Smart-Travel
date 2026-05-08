/**
 * Utility functions for CRON expression parsing and next run time calculation
 */

/**
 * Parse CRON expression into components
 * @param {string} cronExpression - CRON expression (e.g., "0 15 * * *")
 * @returns {object} Parsed CRON components
 */
export function parseCronExpression(cronExpression) {
  const parts = cronExpression.split(' ').filter(part => part.length > 0)
  if (parts.length < 5) {
    throw new Error('Invalid CRON expression')
  }

  return {
    minute: parts[0],
    hour: parts[1],
    day: parts[2],
    month: parts[3],
    dayOfWeek: parts[4]
  }
}

/**
 * Calculate next run time based on CRON expression
 * @param {string} cronExpression - CRON expression
 * @param {string} timezone - Timezone (default: 'UTC')
 * @returns {Date} Next run time
 */
export function calculateNextRunTime(cronExpression, timezone = 'UTC') {
  try {
    const cron = parseCronExpression(cronExpression)
    const now = new Date()
    let nextRun = new Date(now)

    // Handle different CRON patterns
    if (cronExpression === '0 0 * * *') {
      // Daily at midnight
      nextRun.setHours(0, 0, 0, 0)
      if (nextRun <= now) {
        nextRun.setDate(nextRun.getDate() + 1)
      }
    } else if (cronExpression === '0 * * * *') {
      // Hourly
      nextRun.setMinutes(0, 0, 0)
      if (nextRun <= now) {
        nextRun.setHours(nextRun.getHours() + 1)
      }
    } else if (cron.minute === '0' && cron.hour === '0' && cron.day === '*' && cron.month === '*' && cron.dayOfWeek === '*') {
      // Daily at midnight
      nextRun.setHours(0, 0, 0, 0)
      if (nextRun <= now) {
        nextRun.setDate(nextRun.getDate() + 1)
      }
    } else if (cron.minute === '0' && cron.hour !== '*' && cron.day === '*' && cron.month === '*' && cron.dayOfWeek === '*') {
      // Daily at specific hour
      const hour = parseInt(cron.hour)
      nextRun.setHours(hour, 0, 0, 0)
      if (nextRun <= now) {
        nextRun.setDate(nextRun.getDate() + 1)
      }
    } else if (cron.minute === '0' && cron.hour === '*' && cron.day === '*' && cron.month === '*' && cron.dayOfWeek === '*') {
      // Every hour
      nextRun.setMinutes(0, 0, 0)
      if (nextRun <= now) {
        nextRun.setHours(nextRun.getHours() + 1)
      }
    } else if (cron.minute === '0' && cron.hour !== '*' && cron.day !== '*' && cron.month === '*' && cron.dayOfWeek === '*') {
      // Monthly at specific day and hour (e.g., "0 1 1 * *")
      const hour = parseInt(cron.hour)
      const day = parseInt(cron.day)

      // Create target date for this month in UTC
      const targetThisMonth = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), day, hour, 0, 0, 0))

      if (targetThisMonth > now) {
        // This month's target date hasn't passed yet
        nextRun = targetThisMonth
      } else {
        // This month's target has passed, move to next month
        nextRun = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, day, hour, 0, 0, 0))
      }
    } else if (cron.minute === '0' && cron.hour !== '*' && cron.day === '*' && cron.month === '*' && cron.dayOfWeek !== '*') {
      // Weekly at specific day and hour
      const hour = parseInt(cron.hour)
      const dayOfWeek = parseInt(cron.dayOfWeek)
      nextRun.setHours(hour, 0, 0, 0)

      // Find next occurrence of the specified day of week
      const currentDayOfWeek = now.getDay()
      const daysUntilTarget = (dayOfWeek - currentDayOfWeek + 7) % 7

      if (daysUntilTarget === 0 && nextRun <= now) {
        // Same day but time has passed, move to next week
        nextRun.setDate(nextRun.getDate() + 7)
      } else if (daysUntilTarget > 0) {
        nextRun.setDate(nextRun.getDate() + daysUntilTarget)
      } else {
        // Target day is earlier in week, move to next week
        nextRun.setDate(nextRun.getDate() + 7 + daysUntilTarget)
      }
    } else if (cron.minute.startsWith('*/')) {
      // Every N minutes
      const interval = parseInt(cron.minute.substring(2))
      const currentMinutes = now.getMinutes()
      const nextMinute = Math.ceil(currentMinutes / interval) * interval
      nextRun.setMinutes(nextMinute, 0, 0)
      if (nextRun <= now) {
        nextRun.setMinutes(nextRun.getMinutes() + interval)
      }
    } else if (cron.hour.startsWith('*/')) {
      // Every N hours
      const interval = parseInt(cron.hour.substring(2))
      const currentHour = now.getHours()
      const nextHour = Math.ceil(currentHour / interval) * interval
      nextRun.setHours(nextHour, 0, 0, 0)
      if (nextRun <= now) {
        nextRun.setHours(nextRun.getHours() + interval)
      }
    } else {
      // For complex patterns, try to parse basic components
      const minute = cron.minute === '*' ? 0 : parseInt(cron.minute) || 0
      const hour = cron.hour === '*' ? now.getHours() : parseInt(cron.hour) || 0

      nextRun.setMinutes(minute, 0, 0)
      nextRun.setHours(hour)

      if (nextRun <= now) {
        nextRun.setDate(nextRun.getDate() + 1)
      }
    }

    return nextRun
  } catch (error) {
    console.error('Error calculating next run time:', error)
    // Fallback to 1 hour from now
    return new Date(Date.now() + 60 * 60 * 1000)
  }
}

/**
 * Format next run time for display
 * @param {Date} nextRun - Next run time
 * @returns {string} Formatted string
 */
export function formatNextRunTime(nextRun) {
  if (!nextRun) return 'Never'

  const now = new Date()
  const diffMs = nextRun.getTime() - now.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffHours / 24)

  if (diffDays > 0) {
    return `In ${diffDays} day${diffDays > 1 ? 's' : ''} (${nextRun.toLocaleString()})`
  } else if (diffHours > 0) {
    return `In ${diffHours} hour${diffHours > 1 ? 's' : ''} (${nextRun.toLocaleString()})`
  } else {
    return nextRun.toLocaleString()
  }
}