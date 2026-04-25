"use client"

import { use, useEffect, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ArrowLeft, CheckCircle2, XCircle, AlertCircle, Database, FileJson, Clock, Loader2 } from "lucide-react"
import { BackToHomeButton } from "@/components/ui/back-to-home-button"
import apiClient from "../../../services/apiClient.js"

const formatDuration = (duration) => {
  if (!duration) return 'N/A'

  // If duration is in milliseconds (numeric), convert to seconds
  const durationMs = typeof duration === 'number' ? duration : parseFloat(duration)

  if (durationMs < 1000) {
    return `${durationMs}ms`
  } else {
    const seconds = (durationMs / 1000).toFixed(2)
    return `${seconds}s`
  }
}

export default function RunDetailPage({ params }) {
  const { id } = use(params)
  const [run, setRun] = useState(null)
  const [logs, setLogs] = useState([])
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [logsLoading, setLogsLoading] = useState(false)
  const [requestsLoading, setRequestsLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleExportJson = () => {
    if (!run?.extractedData) return

    const dataStr = JSON.stringify(run.extractedData, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)

    const exportFileDefaultName = `run-${run.id}-extracted-data.json`

    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  useEffect(() => {
    apiClient.get(`/api/runs/${id}`)
      .then(res => {
        setRun(res.data)
        setLoading(false)
      })
      .catch(err => {
        setError('Failed to load run details')
        setLoading(false)
      })
  }, [id])

  useEffect(() => {
    if (run) {
      // Fetch logs
      setLogsLoading(true)
      apiClient.get(`/api/runs/${id}/logs`)
        .then(res => {
          setLogs(res.data)
        })
        .catch(err => {
          console.error('Failed to load logs:', err)
          setLogs([])
        })
        .finally(() => {
          setLogsLoading(false)
        })

      // Fetch requests
      setRequestsLoading(true)
      apiClient.get(`/api/runs/${id}/requests`)
        .then(res => {
          setRequests(res.data)
        })
        .catch(err => {
          console.error('Failed to load requests:', err)
          setRequests([])
        })
        .finally(() => {
          setRequestsLoading(false)
        })
    }
  }, [run, id])

  const getLevelIcon = (level) => {
    switch (level) {
      case "error":
        return <XCircle className="h-4 w-4 text-destructive" />
      case "warning":
        return <AlertCircle className="h-4 w-4 text-yellow-500" />
      default:
        return <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
    }
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return new Date()
    return typeof timestamp === 'string' ? new Date(timestamp) : new Date(timestamp)
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-12 w-12 text-muted-foreground mb-4 animate-spin" />
            <p className="text-muted-foreground">Loading run details...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-12">
            <XCircle className="h-12 w-12 text-destructive mb-4" />
            <h3 className="text-lg font-semibold mb-2">Error loading run details</h3>
            <p className="text-muted-foreground text-center">{error}</p>
            <Button asChild className="mt-4">
              <Link href="/runs">Back to Runs</Link>
            </Button>
          </div>
        ) : !run ? (
          <div className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Run not found</h3>
            <p className="text-muted-foreground text-center">The requested run could not be found.</p>
            <Button asChild className="mt-4">
              <Link href="/runs">Back to Runs</Link>
            </Button>
          </div>
        ) : (
          <>
            <div className="mb-8">
              <div className="flex items-center gap-4 mb-4">
                <BackToHomeButton />
                <Button variant="ghost" asChild className="gap-2">
                  <Link href="/runs">
                    <ArrowLeft className="h-4 w-4" />
                    Back to Runs
                  </Link>
                </Button>
              </div>
              <div className="flex items-start justify-between">
                <div>
                  <h1 className="text-3xl font-bold tracking-tight">{run.connectionName}</h1>
                  <p className="text-muted-foreground mt-1">Run ID: {run.id}</p>
                </div>
                <Badge variant="default" className="gap-1">
              <CheckCircle2 className="h-4 w-4" />
              {run.status}
            </Badge>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-4 mb-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Duration</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{formatDuration(run.duration)}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Requests</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{run.successfulRequests}/{run.totalRequests}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Records Extracted</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{run.recordsExtracted}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Records Loaded</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{run.recordsLoaded}</p>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="logs" className="space-y-4">
          <TabsList>
            <TabsTrigger value="logs">Logs</TabsTrigger>
            <TabsTrigger value="requests">Requests</TabsTrigger>
            <TabsTrigger value="data">Extracted Data</TabsTrigger>
          </TabsList>

          <TabsContent value="logs">
            <Card>
              <CardHeader>
                <CardTitle>Execution Logs</CardTitle>
                <CardDescription>Detailed logs from this run</CardDescription>
              </CardHeader>
              <CardContent>
                {logsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 text-muted-foreground animate-spin mr-2" />
                    <span className="text-muted-foreground">Loading logs...</span>
                  </div>
                ) : (
                  <ScrollArea className="h-96">
                    <div className="space-y-2">
                      {logs.length > 0 ? logs.map((log) => (
                        <div key={log.id} className="flex items-start gap-3 p-3 rounded-lg hover:bg-muted/50">
                          {getLevelIcon(log.level)}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm">{log.message}</p>
                            <p className="text-xs text-muted-foreground mt-1">{formatTimestamp(log.timestamp).toLocaleString()}</p>
                          </div>
                        </div>
                      )) : (
                        <div className="text-center py-8 text-muted-foreground">
                          No logs available for this run
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="requests">
            <Card>
              <CardHeader>
                <CardTitle>API Requests</CardTitle>
                <CardDescription>Individual requests made during this run</CardDescription>
              </CardHeader>
              <CardContent>
                {requestsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 text-muted-foreground animate-spin mr-2" />
                    <span className="text-muted-foreground">Loading requests...</span>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {requests.length > 0 ? requests.map((request) => (
                      <div key={request.id} className="p-4 border rounded-lg">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <code className="text-xs bg-muted px-2 py-1 rounded break-all">{request.url}</code>
                          </div>
                          <Badge variant="outline">{request.status}</Badge>
                        </div>
                        <div className="flex items-center gap-6 text-sm">
                          <div>
                            <span className="text-muted-foreground">Response Time:</span>
                            <span className="font-medium ml-2">{request.responseTime}ms</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Records:</span>
                            <span className="font-medium ml-2">{request.recordsExtracted}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Time:</span>
                            <span className="font-medium ml-2">{formatTimestamp(request.timestamp).toLocaleTimeString()}</span>
                          </div>
                        </div>
                      </div>
                    )) : (
                      <div className="text-center py-8 text-muted-foreground">
                        No requests available for this run
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="data">
            <Card>
              <CardHeader>
                <CardTitle>Extracted Data</CardTitle>
                <CardDescription>Preview of data extracted from API responses</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Database className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">{run?.recordsExtracted || 0} records extracted</span>
                    </div>
                    <Button variant="outline" size="sm" className="gap-2 bg-transparent" onClick={handleExportJson}>
                      <FileJson className="h-4 w-4" />
                      Export JSON
                    </Button>
                  </div>
                  <ScrollArea className="h-80 border rounded-lg">
                    {run?.extractedData && Array.isArray(run.extractedData) && run.extractedData.length > 0 ? (
                      <pre className="p-4 text-xs font-mono">{JSON.stringify(run.extractedData.slice(0, 2), null, 2)}</pre>
                    ) : run?.extractedData && (!Array.isArray(run.extractedData) || Object.keys(run.extractedData).length > 0) ? (
                      <pre className="p-4 text-xs font-mono">{JSON.stringify(run.extractedData, null, 2)}</pre>
                    ) : (
                      <div className="p-4 text-center text-muted-foreground">
                        No extracted data available
                      </div>
                    )}
                  </ScrollArea>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
          </>
        )}
      </div>
    </div>
  )
}
