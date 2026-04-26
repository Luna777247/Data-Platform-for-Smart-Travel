'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Plus,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Activity,
  BarChart3,
  Settings,
  Database,
  Calendar,
  Map,
  Eye,
  Zap,
  FileJson,
  ArrowRight,
  CheckSquare,
  Layers,
  Watch,
  PlayCircle,
} from 'lucide-react'
import apiClient from '@/services/apiClient'

export default function HomeDashboard() {
  const router = useRouter()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch status stats
        const statusRes = await apiClient.get('/api/status')
        console.log('[Dashboard] Status response:', statusRes.data)

        const data = statusRes.data
        setStats({
          status: 'healthy', // Assume healthy if API responds
          uptime: data.uptime,
          connections: data.connections?.active || 0,
          schedules: data.schedules?.total || 0,
          totalRuns: data.runs?.total || 0,
          runs24h: data.runs?.last24h || 0,
          successRate: data.activity?.successRate || 0,
        })
        console.log('[Dashboard] Stats set:', {
          status: 'healthy',
          uptime: data.uptime,
          connections: data.connections?.active || 0,
          schedules: data.schedules?.total || 0,
          totalRuns: data.runs?.total || 0,
          runs24h: data.runs?.last24h || 0,
          successRate: data.activity?.successRate || 0,
        })
      } catch (err) {
        console.error('[Dashboard Error]', err)
        console.error('[Dashboard Error details]', err.response?.data, err.message)
        setError('Failed to load dashboard stats')
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  const handleNavigate = (path) => {
    router.push(path)
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-8">
        <Skeleton className="h-16 w-96" />
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      <div className="container mx-auto p-6 space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">Data Platform</h1>
          <p className="text-muted-foreground text-lg">
            No-code API management platform - Integrate, automate, and analyze data
          </p>
        </div>

        {/* Quick Actions */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="flex gap-4 flex-wrap">
          <Button
            size="lg"
            onClick={() => handleNavigate('/connections/new')}
            className="gap-2"
          >
            <Plus className="h-5 w-5" />
            New Connection
          </Button>
          <Button
            variant="outline"
            size="lg"
            onClick={() => handleNavigate('/dashboards/smart-travel')}
            className="gap-2"
          >
            <BarChart3 className="h-5 w-5" />
            Smart Travel Analytics
          </Button>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Watch className="h-4 w-4 text-blue-500" />
                Uptime
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {stats?.status === 'healthy' ? '✓ Healthy' : '⚠ Down'}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats?.uptime || 'N/A'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <PlayCircle className="h-4 w-4 text-purple-500" />
                Total Runs
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.totalRuns || '--'}</div>
              <p className="text-xs text-muted-foreground">all time</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Clock className="h-4 w-4 text-orange-500" />
                24h Runs
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.runs24h || '--'}</div>
              <p className="text-xs text-muted-foreground">last 24 hours</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                Success Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.successRate ? `${stats.successRate}%` : '--'}</div>
              <p className="text-xs text-muted-foreground">pass rate</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Database className="h-4 w-4 text-cyan-500" />
                Connections
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.connections}</div>
              <p className="text-xs text-muted-foreground">active</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Calendar className="h-4 w-4 text-indigo-500" />
                Schedules
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.schedules || '--'}</div>
              <p className="text-xs text-muted-foreground">configured</p>
            </CardContent>
          </Card>
        </div>

        {/* Platform Features */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Core Features */}
          <div className="space-y-4">
            <div className="space-y-2 mb-4">
              <h2 className="text-2xl font-bold">Core Features</h2>
              <p className="text-muted-foreground">Essential tools for data integration</p>
            </div>

            <Card
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => handleNavigate('/connections')}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="h-5 w-5 text-blue-500" />
                    <CardTitle>API Connections</CardTitle>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </div>
                <CardDescription>
                  Manage your API connections, configure endpoints, parameters, and authentication
                </CardDescription>
              </CardHeader>
            </Card>

            <Card
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => handleNavigate('/schedules')}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-5 w-5 text-green-500" />
                    <CardTitle>Schedules</CardTitle>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </div>
                <CardDescription>
                  Set up automated runs with daily, weekly, monthly, or custom CRON schedules
                </CardDescription>
              </CardHeader>
            </Card>

            <Card
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => handleNavigate('/runs')}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-orange-500" />
                    <CardTitle>Run History</CardTitle>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </div>
                <CardDescription>
                  View execution history, logs, and monitor the status of your API runs
                </CardDescription>
              </CardHeader>
            </Card>
          </div>

          {/* Advanced Features */}
          <div className="space-y-4">
            <div className="space-y-2 mb-4">
              <h2 className="text-2xl font-bold">Advanced Tools</h2>
              <p className="text-muted-foreground">Power-user capabilities</p>
            </div>

            <Card
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => handleNavigate('/data')}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Eye className="h-5 w-5 text-purple-500" />
                    <CardTitle>Data Explorer</CardTitle>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </div>
                <CardDescription>
                  Browse extracted data, view transformations, and export to your data warehouse
                </CardDescription>
              </CardHeader>
            </Card>

            <Card
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => handleNavigate('/mappings')}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Map className="h-5 w-5 text-cyan-500" />
                    <CardTitle>Field Mappings</CardTitle>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </div>
                <CardDescription>
                  Configure how API response fields map to your database schema
                </CardDescription>
              </CardHeader>
            </Card>

            <Card
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => handleNavigate('/analytics')}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-indigo-500" />
                    <CardTitle>Analytics Dashboards</CardTitle>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </div>
                <CardDescription>
                  Interactive dashboards with real-time ETL performance and data quality metrics
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>

        {/* Platform Capabilities */}
        <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-500" />
              Platform Capabilities
            </CardTitle>
            <CardDescription>Powerful features built for data integration at scale</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="flex gap-3">
                <CheckSquare className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-sm">Multi-Parameter Support</p>
                  <p className="text-xs text-muted-foreground">
                    List, Cartesian product, and template modes
                  </p>
                </div>
              </div>

              <div className="flex gap-3">
                <CheckSquare className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-sm">Dynamic Parameters</p>
                  <p className="text-xs text-muted-foreground">
                    Date ranges, incremental IDs, and custom logic
                  </p>
                </div>
              </div>

              <div className="flex gap-3">
                <CheckSquare className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-sm">Automatic Schema Detection</p>
                  <p className="text-xs text-muted-foreground">
                    Parse JSON responses and suggest mappings
                  </p>
                </div>
              </div>

              <div className="flex gap-3">
                <CheckSquare className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-sm">Full ETL Pipeline</p>
                  <p className="text-xs text-muted-foreground">
                    Extract, transform, and load to data warehouse
                  </p>
                </div>
              </div>

              <div className="flex gap-3">
                <CheckSquare className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-sm">Flexible Scheduling</p>
                  <p className="text-xs text-muted-foreground">
                    CRON expressions and preset intervals
                  </p>
                </div>
              </div>

              <div className="flex gap-3">
                <CheckSquare className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-sm">Comprehensive Logging</p>
                  <p className="text-xs text-muted-foreground">
                    Track every request and transformation
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Getting Started */}
        <Card className="border-2 border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="text-xl">🚀 Getting Started</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm">
              Click <Badge className="mx-1">New Connection</Badge> to create your first API integration
              and start extracting data automatically
            </p>
            <div className="flex gap-2">
              <Button onClick={() => handleNavigate('/connections/new')} className="gap-2">
                <Plus className="h-4 w-4" />
                Create First Connection
              </Button>
              <Button
                variant="outline"
                onClick={() => handleNavigate('/dashboards/smart-travel')}
                className="gap-2"
              >
                <BarChart3 className="h-4 w-4" />
                View Smart Travel Demo
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
