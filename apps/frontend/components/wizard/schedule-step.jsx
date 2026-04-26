'use client'

import { useState, useEffect } from 'react'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Calendar, Clock, Info } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { calculateNextRunTime, formatNextRunTime } from '@/lib/cron-utils'

export function ScheduleStep({ data, onChange }) {
  const [scheduleType, setScheduleType] = useState(data.type || detectScheduleType(data.cronExpression) || 'daily')
  const [nextRunTime, setNextRunTime] = useState(null)

  const updateSchedule = (field, value) => {
    onChange({ ...data, [field]: value })
  }

  // Calculate next run time when CRON expression changes
  useEffect(() => {
    if (data.cronExpression && data.enabled) {
      try {
        const nextRun = calculateNextRunTime(data.cronExpression)
        setNextRunTime(nextRun)

        // Auto-detect schedule type from CRON expression
        const detectedType = detectScheduleType(data.cronExpression)
        if (detectedType !== data.type) {
          updateSchedule('type', detectedType)
        }
      } catch (error) {
        console.error('Error calculating next run time:', error)
        setNextRunTime(null)
      }
    } else {
      setNextRunTime(null)
    }
  }, [data.cronExpression, data.enabled, data.type])

  // Update local scheduleType when data.type changes
  useEffect(() => {
    const detectedType = detectScheduleType(data.cronExpression) || 'daily'
    setScheduleType(data.type || detectedType)
  }, [data.type, data.cronExpression])

  const generateCronExpression = (type, config = {}) => {
    switch (type) {
      case 'daily':
        return `0 ${config.hour || 0} * * *`
      case 'weekly':
        return `0 ${config.hour || 0} * * ${config.dayOfWeek || 0}`
      case 'monthly':
        return `0 ${config.hour || 0} ${config.dayOfMonth || 1} * *`
      case 'hourly':
        return `0 * * * *`
      default:
        return '0 0 * * *'
    }
  }

  // Detect schedule type from CRON expression
  const detectScheduleType = (cronExpression) => {
    if (!cronExpression) return 'daily'

    const parts = cronExpression.split(' ')
    if (parts.length < 5) return 'daily'

    const [minute, hour, day, month, dayOfWeek] = parts

    if (minute === '0' && hour === '*' && day === '*' && month === '*' && dayOfWeek === '*') {
      return 'hourly'
    } else if (minute === '0' && hour !== '*' && day === '*' && month === '*' && dayOfWeek === '*') {
      return 'daily'
    } else if (minute === '0' && hour !== '*' && day === '*' && month === '*' && dayOfWeek !== '*') {
      return 'weekly'
    } else if (minute === '0' && hour !== '*' && day !== '*' && month === '*' && dayOfWeek === '*') {
      return 'monthly'
    } else {
      return 'custom'
    }
  }

  return (
    <div className="space-y-6">
      {/* Enable Scheduling */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Enable Automated Scheduling</CardTitle>
              <CardDescription>Run this API connection automatically on a schedule</CardDescription>
            </div>
            <Switch checked={data.enabled} onCheckedChange={(checked) => updateSchedule('enabled', checked)} />
          </div>
        </CardHeader>
      </Card>

      {data.enabled && (
        <>
          {/* Schedule Type */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Schedule Type</CardTitle>
              <CardDescription>Choose how frequently to run this API connection</CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs
                value={scheduleType}
                onValueChange={(value) => {
                  setScheduleType(value)
                  updateSchedule('type', value)
                  // Set default CRON expression based on type
                  let defaultCron = '0 0 * * *'
                  switch (value) {
                    case 'hourly':
                      defaultCron = '0 * * * *'
                      break
                    case 'daily':
                      defaultCron = '0 9 * * *' // 9 AM daily
                      break
                    case 'weekly':
                      defaultCron = '0 9 * * 1' // Monday 9 AM
                      break
                    case 'monthly':
                      defaultCron = '0 9 1 * *' // 1st of month 9 AM
                      break
                  }
                  updateSchedule('cronExpression', defaultCron)
                }}
              >
                <TabsList className="grid w-full grid-cols-5">
                  <TabsTrigger value="once">Once</TabsTrigger>
                  <TabsTrigger value="hourly">Hourly</TabsTrigger>
                  <TabsTrigger value="daily">Daily</TabsTrigger>
                  <TabsTrigger value="weekly">Weekly</TabsTrigger>
                  <TabsTrigger value="monthly">Monthly</TabsTrigger>
                </TabsList>

                <TabsContent value="once" className="space-y-4 mt-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Label htmlFor="onceDate">Run Date</Label>
                      <Input id="onceDate" type="date" className="mt-1.5" />
                    </div>
                    <div>
                      <Label htmlFor="onceTime">Run Time</Label>
                      <Input id="onceTime" type="time" className="mt-1.5" />
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="hourly" className="space-y-4 mt-4">
                  <div className="p-4 bg-muted/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      <p className="text-sm font-medium">Runs every hour at minute 0</p>
                    </div>
                    <p className="text-xs text-muted-foreground">The API will be called at the start of every hour (e.g., 1:00, 2:00, 3:00)</p>
                  </div>
                </TabsContent>

                <TabsContent value="daily" className="space-y-4 mt-4">
                  <div>
                    <Label htmlFor="dailyTime">Run Time</Label>
                    <Input
                      id="dailyTime"
                      type="time"
                      className="mt-1.5"
                      value={data.cronExpression ? (() => {
                        const cron = data.cronExpression.split(' ')
                        if (cron.length >= 2) {
                          const hour = cron[1]
                          return `${hour}:00`
                        }
                        return '09:00'
                      })() : '09:00'}
                      onChange={(e) => {
                        const [hour] = e.target.value.split(':')
                        updateSchedule('cronExpression', `0 ${hour} * * *`)
                      }}
                    />
                    <p className="text-xs text-muted-foreground mt-1">API will run every day at this time</p>
                  </div>
                </TabsContent>

                <TabsContent value="weekly" className="space-y-4 mt-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Label htmlFor="weeklyDay">Day of Week</Label>
                      <Select
                        value={data.cronExpression ? (() => {
                          const cron = data.cronExpression.split(' ')
                          if (cron.length >= 5) {
                            return cron[4]
                          }
                          return '1'
                        })() : '1'}
                        onValueChange={(dayOfWeek) => {
                          const cron = data.cronExpression ? data.cronExpression.split(' ') : ['0', '9', '*', '*', '1']
                          cron[4] = dayOfWeek
                          updateSchedule('cronExpression', cron.join(' '))
                        }}
                      >
                        <SelectTrigger id="weeklyDay" className="mt-1.5">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">Sunday</SelectItem>
                          <SelectItem value="1">Monday</SelectItem>
                          <SelectItem value="2">Tuesday</SelectItem>
                          <SelectItem value="3">Wednesday</SelectItem>
                          <SelectItem value="4">Thursday</SelectItem>
                          <SelectItem value="5">Friday</SelectItem>
                          <SelectItem value="6">Saturday</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="weeklyTime">Run Time</Label>
                      <Input
                        id="weeklyTime"
                        type="time"
                        className="mt-1.5"
                        value={data.cronExpression ? (() => {
                          const cron = data.cronExpression.split(' ')
                          if (cron.length >= 2) {
                            const hour = cron[1]
                            return `${hour}:00`
                          }
                          return '09:00'
                        })() : '09:00'}
                        onChange={(e) => {
                          const [hour] = e.target.value.split(':')
                          const cron = data.cronExpression ? data.cronExpression.split(' ') : ['0', '9', '*', '*', '1']
                          cron[1] = hour
                          updateSchedule('cronExpression', cron.join(' '))
                        }}
                      />
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="monthly" className="space-y-4 mt-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Label htmlFor="monthlyDay">Day of Month</Label>
                      <Select
                        value={data.cronExpression ? (() => {
                          const cron = data.cronExpression.split(' ')
                          if (cron.length >= 3) {
                            return cron[2]
                          }
                          return '1'
                        })() : '1'}
                        onValueChange={(dayOfMonth) => {
                          const cron = data.cronExpression ? data.cronExpression.split(' ') : ['0', '9', '1', '*', '*']
                          cron[2] = dayOfMonth
                          updateSchedule('cronExpression', cron.join(' '))
                        }}
                      >
                        <SelectTrigger id="monthlyDay" className="mt-1.5">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {Array.from({ length: 31 }, (_, i) => i + 1).map((day) => (
                            <SelectItem key={day} value={day.toString()}>
                              {day}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="monthlyTime">Run Time</Label>
                      <Input
                        id="monthlyTime"
                        type="time"
                        className="mt-1.5"
                        value={data.cronExpression ? (() => {
                          const cron = data.cronExpression.split(' ')
                          if (cron.length >= 2) {
                            const hour = cron[1]
                            return `${hour}:00`
                          }
                          return '09:00'
                        })() : '09:00'}
                        onChange={(e) => {
                          const [hour] = e.target.value.split(':')
                          const cron = data.cronExpression ? data.cronExpression.split(' ') : ['0', '9', '1', '*', '*']
                          cron[1] = hour
                          updateSchedule('cronExpression', cron.join(' '))
                        }}
                      />
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Advanced CRON */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Advanced: Custom CRON Expression</CardTitle>
              <CardDescription>For advanced users who need custom scheduling patterns</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="cronExpression">CRON Expression</Label>
                <Input
                  id="cronExpression"
                  value={data.cronExpression}
                  onChange={(e) => updateSchedule('cronExpression', e.target.value)}
                  className="mt-1.5 font-mono"
                  placeholder="0 0 * * *"
                />
                <p className="text-xs text-muted-foreground mt-1">Format: minute hour day month day-of-week</p>
              </div>

              <div className="p-3 bg-muted/50 rounded-lg">
                <div className="flex items-start gap-2">
                  <Info className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                  <div className="space-y-1 text-xs">
                    <p className="font-medium">Common CRON Patterns:</p>
                    <div className="space-y-1 text-muted-foreground">
                      <p>
                        <code className="bg-muted px-1 py-0.5 rounded">0 0 * * *</code> - Daily at midnight
                      </p>
                      <p>
                        <code className="bg-muted px-1 py-0.5 rounded">0 */6 * * *</code> - Every 6 hours
                      </p>
                      <p>
                        <code className="bg-muted px-1 py-0.5 rounded">0 9 * * 1</code> - Every Monday at 9 AM
                      </p>
                      <p>
                        <code className="bg-muted px-1 py-0.5 rounded">0 0 1 * *</code> - First day of every month
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Retry Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Retry Configuration</CardTitle>
              <CardDescription>Configure retry behavior for failed runs</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="maxRetries">Max Retries</Label>
                  <Select defaultValue="3">
                    <SelectTrigger id="maxRetries" className="mt-1.5">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="0">No retries</SelectItem>
                      <SelectItem value="1">1 retry</SelectItem>
                      <SelectItem value="3">3 retries</SelectItem>
                      <SelectItem value="5">5 retries</SelectItem>
                      <SelectItem value="10">10 retries</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="retryDelay">Retry Delay (seconds)</Label>
                  <Select defaultValue="60">
                    <SelectTrigger id="retryDelay" className="mt-1.5">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="30">30 seconds</SelectItem>
                      <SelectItem value="60">1 minute</SelectItem>
                      <SelectItem value="300">5 minutes</SelectItem>
                      <SelectItem value="600">10 minutes</SelectItem>
                      <SelectItem value="1800">30 minutes</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Next Run Preview */}
          <Card className="bg-muted/30">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <Calendar className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Next Scheduled Run</p>
                  <p className="text-sm text-muted-foreground">
                    {data.enabled && data.cronExpression
                      ? formatNextRunTime(nextRunTime)
                      : 'Enable scheduling to see next run time'
                    }
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
