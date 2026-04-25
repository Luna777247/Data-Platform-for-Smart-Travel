'use client'

import { useEffect, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { PlayCircle, Clock, CheckCircle2, XCircle, AlertCircle, Search, Filter, Eye, Trash2, RotateCcw, Loader2 } from "lucide-react"
import { PageLayout } from "@/components/ui/page-layout"
import apiClient from "../../services/apiClient.js"

export default function RunsPage() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [timeFilter, setTimeFilter] = useState("24hours")
  const [deletingId, setDeletingId] = useState(null)
  const handleDeleteRun = async (runId) => {
    if (!confirm('Are you sure you want to delete this run? This action cannot be undone.')) {
      return
    }
    
    setDeletingId(runId)
    try {
      try {
        // Try with plural endpoint first
        await apiClient.delete(`/api/runs/${runId}`)
      } catch (err) {
        if (err.response?.status === 404) {
          console.log('Run not found on server, removing from UI...')
          // Still remove from UI even if not found on server
        } else {
          throw err
        }
      }
      
      // Update the UI by removing the deleted run
      setRuns(prevRuns => prevRuns.filter(run => run.id !== runId))
    } catch (err) {
      console.error('Error deleting run:', err)
      setError('Failed to delete run. ' + (err.response?.data?.message || 'Please try again.'))
    } finally {
      setDeletingId(null)
    }
  }

  useEffect(() => {
    apiClient.get('/api/runs')
      .then(res => {
        console.log('[DEBUG] Full API Response:', res)
        const data = res?.data || {}
        const runsData = Array.isArray(data) ? data : (data.runs || [])
        console.log('[DEBUG] Extracted runs:', runsData)
        setRuns(runsData)
        setLoading(false)
      })
      .catch(err => {
        console.error('[DEBUG] Error loading runs:', err)
        setError('Failed to load runs')
        setLoading(false)
      })
  }, [])

  // Filter runs based on search, status, and time
  const filteredRuns = runs.filter(run => {
    // Search filter
    if (searchTerm && !run.connectionName?.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false
    }

    // Status filter
    if (statusFilter !== "all" && run.status !== statusFilter) {
      return false
    }

    // Time filter
    if (timeFilter !== "all" && run.startedAt) {
      const runDate = new Date(run.startedAt)
      const now = new Date()
      const diffMs = now - runDate
      const diffHours = diffMs / (1000 * 60 * 60)
      const diffDays = diffHours / 24

      if (timeFilter === "24hours" && diffHours > 24) return false
      if (timeFilter === "7days" && diffDays > 7) return false
      if (timeFilter === "30days" && diffDays > 30) return false
    }

    return true
  })

  const getStatusIcon = (status) => {
    switch (status) {
      case "success":
        return <CheckCircle2 className="h-4 w-4" />
      case "failed":
        return <XCircle className="h-4 w-4" />
      case "running":
        return <Clock className="h-4 w-4 animate-spin" />
      case "partial":
        return <AlertCircle className="h-4 w-4" />
      default:
        return <PlayCircle className="h-4 w-4" />
    }
  }

  const getStatusVariant = (status) => {
    switch (status) {
      case "success":
        return "default"
      case "failed":
        return "destructive"
      case "running":
        return "secondary"
      case "pending":
        return "outline"
      default:
        return "outline"
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case "success":
        return "bg-green-100 text-green-800"
      case "failed":
        return "bg-red-100 text-red-800"
      case "running":
        return "bg-blue-100 text-blue-800"
      case "pending":
        return "bg-yellow-100 text-yellow-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  return (
    <PageLayout
      title="Run History"
      description="View and monitor API execution history"
      showBackButton={true}
      icon={<div className="p-2 bg-gradient-to-br from-green-100 to-green-50 rounded-lg"><PlayCircle className="h-6 w-6 text-green-600" /></div>}
    >

        <Card className="mb-6">
          <CardContent className="pt-6" suppressHydrationWarning={true}>
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="flex-1 min-w-0 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground flex-shrink-0" />
                <Input 
                  placeholder="Search by connection name..." 
                  className="pl-10 pr-4"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <div className="flex flex-wrap gap-2 justify-center lg:justify-end">
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-full sm:w-48">
                    <Filter className="h-4 w-4 mr-2 flex-shrink-0" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="success">Success</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                    <SelectItem value="running">Running</SelectItem>
                    <SelectItem value="partial">Partial</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={timeFilter} onValueChange={setTimeFilter}>
                  <SelectTrigger className="w-full sm:w-48">
                    <Clock className="h-4 w-4 mr-2 flex-shrink-0" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="24hours">Last 24 Hours</SelectItem>
                    <SelectItem value="7days">Last 7 Days</SelectItem>
                    <SelectItem value="30days">Last 30 Days</SelectItem>
                    <SelectItem value="all">All Time</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {loading ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12" suppressHydrationWarning={true}>
              <Clock className="h-12 w-12 text-muted-foreground mb-4 animate-spin" />
              <p className="text-muted-foreground">Loading runs...</p>
            </CardContent>
          </Card>
        ) : error ? (
          <Card className="border-destructive">
            <CardContent className="flex flex-col items-center justify-center py-12" suppressHydrationWarning={true}>
              <XCircle className="h-12 w-12 text-destructive mb-4" />
              <h3 className="text-lg font-semibold mb-2">Error loading runs</h3>
              <p className="text-muted-foreground text-center">{error}</p>
            </CardContent>
          </Card>
        ) : runs.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12" suppressHydrationWarning={true}>
              <PlayCircle className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No runs yet</h3>
              <p className="text-muted-foreground text-center mb-4 text-pretty max-w-md">
                API runs will appear here once you execute a connection
              </p>
              <Link href="/connections">
                <Button>View Connections</Button>
              </Link>
            </CardContent>
          </Card>
        ) : filteredRuns.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12" suppressHydrationWarning={true}>
              <Search className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No runs found</h3>
              <p className="text-muted-foreground text-center">
                Try adjusting your filters
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4" suppressHydrationWarning={true}>
            {filteredRuns.map((run) => {
              const duration = run.executionTime 
                ? `${Math.floor(run.executionTime / 1000)}s` 
                : "In progress..."
              const startDate = new Date(run.startedAt)
              const completedDate = run.completedAt ? new Date(run.completedAt) : null
              return (
                <Card key={run.id} className="group hover:shadow-lg transition-all duration-200 border-l-4 border-l-blue-500 hover:border-l-purple-500 overflow-hidden">
                  <CardHeader className="pb-3">
                    <div className="flex flex-col gap-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 mb-2 flex-wrap">
                            <CardTitle className="text-lg truncate group-hover:text-blue-600 transition-colors">
                              Connection: {run.connectionName || run.connectionId}
                            </CardTitle>
                            <Badge variant={getStatusVariant(run.status)} className={`gap-1 flex-shrink-0 ${getStatusColor(run.status)}`}>
                              {getStatusIcon(run.status)}
                              <span className="hidden sm:inline capitalize">{run.status}</span>
                              <span className="sm:hidden">{run.status.charAt(0).toUpperCase()}</span>
                            </Badge>
                          </div>
                          <CardDescription className="line-clamp-1">
                            Started {startDate.toLocaleString()}
                            {completedDate && ` • Completed ${completedDate.toLocaleString()}`}
                          </CardDescription>
                          {run.metadata?.apiUrl && (
                            <p className="text-xs text-foreground/70 mt-1 font-mono truncate">
                              {run.metadata.method || 'GET'} {run.metadata.apiUrl}
                            </p>
                          )}
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0 sm:flex-col">
                          <Link href={`/runs/${run.id}`}>
                            <Button variant="outline" size="sm" className="gap-2">
                              <Eye className="h-4 w-4" />
                              <span className="hidden sm:inline">View</span>
                            </Button>
                          </Link>
                          <Button 
                            variant="outline"
                            size="sm" 
                            className="gap-2 text-destructive hover:text-destructive hover:bg-destructive/10"
                            onClick={(e) => {
                              e.preventDefault()
                              e.stopPropagation()
                              handleDeleteRun(run.id)
                            }}
                            disabled={deletingId === run.id}
                          >
                            {deletingId === run.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                            <span className="hidden sm:inline">{deletingId === run.id ? 'Deleting...' : 'Delete'}</span>
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent suppressHydrationWarning={true}>
                    <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-blue-500 flex-shrink-0" />
                        <div className="min-w-0">
                          <p className="text-xs text-muted-foreground">Duration</p>
                          <p className="text-sm font-medium truncate">{duration}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <RotateCcw className="h-4 w-4 text-purple-500 flex-shrink-0" />
                        <div className="min-w-0">
                          <p className="text-xs text-muted-foreground">Requests</p>
                          <p className="text-sm font-medium">{run.successfulRequests}/{run.totalRequests}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />
                        <div className="min-w-0">
                          <p className="text-xs text-muted-foreground">Success Rate</p>
                          <p className="text-sm font-medium">{run.totalRequests > 0 ? Math.round((run.successfulRequests / run.totalRequests) * 100) : 0}%</p>
                        </div>
                      </div>
                      <div className="hidden sm:flex items-center gap-2">
                        <AlertCircle className="h-4 w-4 text-orange-500 flex-shrink-0" />
                        <div className="min-w-0">
                          <p className="text-xs text-muted-foreground">Records</p>
                          <p className="text-sm font-medium">{run.recordsProcessed}</p>
                        </div>
                      </div>
                      <div className="hidden lg:flex items-center gap-2">
                        <XCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
                        <div className="min-w-0">
                          <p className="text-xs text-muted-foreground">Failed</p>
                          <p className="text-sm font-medium">{run.failedRequests}</p>
                        </div>
                      </div>
                    </div>
                    {run.errors && (
                      <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                        <p className="text-sm text-destructive line-clamp-2">{JSON.stringify(run.errors)}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
    </PageLayout>
  )
}
