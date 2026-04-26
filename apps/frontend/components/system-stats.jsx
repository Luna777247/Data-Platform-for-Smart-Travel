'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Activity, Clock, Zap, CheckCircle, AlertCircle } from 'lucide-react'
import apiClient from '../services/apiClient.js'

export function SystemStats() {
  const [stats, setStats] = useState({
    uptime: '--',
    totalRuns: '--',
    last24hRuns: '--',
    successRate: '--',
    activeConnections: '--',
    totalSchedules: '--'
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function fetchStats() {
      try {
        console.log('[SystemStats] Starting fetch from /api/status...')
        
        const response = await apiClient.get('/api/status', {
          validateStatus: () => true // Accept all status codes
        })
        
        console.log('[SystemStats] Response received:', {
          status: response.status,
          statusText: response.statusText,
          data: response.data
        })
        
        if (response.status === 200 && response.data) {
          const data = response.data
          console.log('[SystemStats] Processing data:', data)

          setStats({
            uptime: data.uptime || '--',
            totalRuns: (data.runs?.total !== undefined) ? data.runs.total.toString() : '--',
            last24hRuns: (data.runs?.last24h !== undefined) ? data.runs.last24h.toString() : '--',
            successRate: (data.activity?.successRate !== undefined) ? data.activity.successRate.toFixed(2) + '%' : '--',
            activeConnections: (data.connections?.active !== undefined) ? data.connections.active.toString() : '--',
            totalSchedules: (data.schedules?.total !== undefined) ? data.schedules.total.toString() : '--'
          })
          setError(null)
          console.log('[SystemStats] Stats updated successfully')
        } else {
          throw new Error(`API returned status ${response.status}`)
        }
      } catch (err) {
        const errorMsg = err.message || 'Unknown error'
        console.error('[SystemStats] Error fetching stats:', {
          message: errorMsg,
          url: err.config?.url,
          baseURL: err.config?.baseURL,
          code: err.code,
          response: err.response?.data
        })
        setError(errorMsg)
        setStats({
          uptime: '--',
          totalRuns: '--',
          last24hRuns: '--',
          successRate: '--',
          activeConnections: '--',
          totalSchedules: '--'
        })
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  if (error) {
    return (
      <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center gap-2 text-red-800">
          <AlertCircle className="h-5 w-5" />
          <div>
            <p className="font-semibold">Unable to fetch system stats</p>
            <p className="text-sm">{error}</p>
            <p className="text-xs text-red-600 mt-2">
              Make sure the backend API is running at {process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-6 mb-6">
      {/* Uptime */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">Uptime</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.uptime}</div>
        </CardContent>
      </Card>

      {/* Total Runs */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Runs</CardTitle>
            <Zap className="h-4 w-4 text-yellow-500" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalRuns}</div>
        </CardContent>
      </Card>

      {/* Last 24h Runs */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">24h Runs</CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.last24hRuns}</div>
        </CardContent>
      </Card>

      {/* Success Rate */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">Success Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.successRate}</div>
        </CardContent>
      </Card>

      {/* Active Connections */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">Connections</CardTitle>
            <Zap className="h-4 w-4 text-orange-500" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.activeConnections}</div>
        </CardContent>
      </Card>

      {/* Total Schedules */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">Schedules</CardTitle>
            <Clock className="h-4 w-4 text-purple-500" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalSchedules}</div>
        </CardContent>
      </Card>
    </div>
  )
}
