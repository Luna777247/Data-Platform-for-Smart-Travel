// frontendphp/app/dashboards/pipeline-monitor/page.jsx
'use client'

import { useState, useEffect } from 'react'
import { PageLayout } from '@/components/ui/page-layout'
import { OverviewCards } from '@/components/pipeline-monitor/overview-cards'
import { PipelineTable } from '@/components/pipeline-monitor/pipeline-table'
import { Charts } from '@/components/pipeline-monitor/charts'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Activity, RefreshCcw, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import apiClient from '@/services/apiClient'

export default function PipelineMonitorPage() {
    const [data, setData] = useState([])
    const [metrics, setMetrics] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [lastRefreshed, setLastRefreshed] = useState(new Date())

    const fetchData = async () => {
        try {
            // Parallel fetch from the two new production endpoints
            const [statusRes, metricsRes] = await Promise.all([
                apiClient.get('/api/pipeline/status'),
                apiClient.get('/api/dashboard/pipeline-metrics')
            ])

            setData(statusRes.data || [])

            // Calculate overview metrics from status data and aggregation
            const statusData = statusRes.data || []
            const runningJobs = statusData.filter(j => j.status === 'running').length
            const failedJobs = statusData.filter(j => j.status === 'failed').length
            const doneJobs = statusData.filter(j => j.status === 'done').length

            const totalCollected = statusData.reduce((sum, j) => sum + (j.collected || 0), 0)
            const totalTarget = statusData.reduce((sum, j) => sum + (j.target || 0), 0)

            setMetrics({
                total_jobs: statusData.length,
                running_jobs: runningJobs,
                failed_jobs: failedJobs,
                completed_jobs: doneJobs,
                total_collected: totalCollected,
                total_target: totalTarget
            })

            setError(null)
            setLastRefreshed(new Date())
        } catch (err) {
            console.error('Failed to fetch pipeline metrics:', err)
            setError('Could not connect to the pipeline service. Please ensure the backend is running.')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData()
        // Auto refresh every 10 seconds for real-time monitoring
        const interval = setInterval(fetchData, 10000)
        return () => clearInterval(interval)
    }, [])

    if (loading && !data.length) {
        return (
            <PageLayout
                title="Pipeline Monitor"
                description="Real-time tracking for Smart Tourism data collectors"
                icon={<Activity className="h-6 w-6 text-blue-600" />}
            >
                <div className="space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24 rounded-xl" />)}
                    </div>
                    <Skeleton className="h-96 rounded-xl" />
                </div>
            </PageLayout>
        )
    }

    return (
        <PageLayout
            title="Pipeline Monitor"
            description="Real-time tracking for Smart Tourism data collectors"
            icon={<Activity className="h-6 w-6 text-blue-100" />}
            actions={
                <div className="flex items-center gap-3">
                    <span className="text-[10px] text-muted-foreground uppercase font-medium">
                        Last updated: {lastRefreshed.toLocaleTimeString()}
                    </span>
                    <Button variant="outline" size="sm" onClick={() => { setLoading(true); fetchData(); }}>
                        <RefreshCcw className={`h-3 w-3 mr-1 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                </div>
            }
        >
            <div className="space-y-8 pb-10">
                {error && (
                    <Alert variant="destructive" className="bg-red-50 border-red-200">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                {/* 1. Overview Section */}
                <OverviewCards metrics={metrics} />

                {/* 2. Visualizations */}
                <Charts data={data} />

                {/* 3. Detailed Jobs Table */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="text-lg font-semibold text-slate-800 tracking-tight">Active & Historical Pipelines</h3>
                        <div className="flex gap-2">
                            <div className="flex items-center gap-1.5 px-2 py-1 bg-green-50 text-green-700 text-[10px] font-bold rounded-md border border-green-100 uppercase">
                                <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
                                Ready
                            </div>
                        </div>
                    </div>
                    <PipelineTable data={data} />
                </div>
            </div>
        </PageLayout>
    )
}
