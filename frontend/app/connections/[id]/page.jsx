'use client'

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { 
  ArrowLeft, 
  Play, 
  Settings, 
  Database, 
  Clock, 
  CheckCircle, 
  XCircle,
  Activity,
  ExternalLink,
  Edit
} from "lucide-react"
import { BackToHomeButton } from "@/components/ui/back-to-home-button"
import apiClient from "../../../services/apiClient.js"

export default function ConnectionDetailPage() {
  const params = useParams()
  const router = useRouter()
  const connectionId = Array.isArray(params?.id) ? params.id[0] : params?.id

  const [connection, setConnection] = useState(null)
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [testResult, setTestResult] = useState(null)
  const [testingConnection, setTestingConnection] = useState(false)

  useEffect(() => {
    async function fetchConnectionDetails() {
      try {
        if (!connectionId) return
        setLoading(true)
        const connectionRes = await apiClient.get(`/api/connections/${connectionId}`)
        console.log('Raw connection data from API:', connectionRes.data)
        console.log('Connection authType from API:', connectionRes.data.authType)
        console.log('Connection authConfig from API:', connectionRes.data.authConfig)
        console.log('Connection baseUrl from API:', connectionRes.data.baseUrl)
        console.log('Connection method from API:', connectionRes.data.method)
        console.log('Connection headers from API:', connectionRes.data.headers)
        setConnection(connectionRes.data)
        const runsRes = await apiClient.get(`/api/runs`, { params: { connectionId: connectionRes.data.connectionId, limit: 10 } })
        const runsData = runsRes.data?.runs || []
        const totalRunsCount = runsRes.data?.total || runsData.length  // Use total from API, fallback to length
        setRuns(runsData)
        
        // Calculate statistics from runs
        const successfulRuns = runsData.filter(run => run.status === 'success').length
        const successRate = totalRunsCount > 0 ? Math.round((successfulRuns / totalRunsCount) * 100) : 0
        const lastRun = runsData.length > 0 ? runsData[0].startedAt : null
        
        // Update connection with calculated stats
        setConnection(prev => ({
          ...prev,
          totalRuns: totalRunsCount,
          successRate,
          lastRun
        }))
      } catch (err) {
        console.error('[v0] Error fetching connection:', err)
        setError(err instanceof Error ? err.message : 'Failed to load connection')
      } finally {
        setLoading(false)
      }
    }
    fetchConnectionDetails()
  }, [connectionId])

  const handleTestConnection = async () => {
    if (!connection) return
    setTestingConnection(true)
    setTestResult(null)
    try {
      // Convert headers array to key-value object for API
      const headersObject = {}
      if (Array.isArray(connection.headers)) {
        connection.headers.forEach(header => {
          if (typeof header === 'object') {
            if (header.key && header.value) {
              headersObject[header.key] = header.value
            } else if (Object.keys(header).length === 1) {
              const [key, value] = Object.entries(header)[0]
              headersObject[key] = value
            }
            // Skip empty objects
          }
        })
      }

      const testData = {
        apiConfig: {
          baseUrl: connection.baseUrl,
          method: connection.method,
          headers: headersObject,
          authType: connection.authType || 'none',
          authConfig: connection.authConfig || {}
        }
      }
      
      console.log('About to make API call to /api/test-connection')
      console.log('Test data being sent:', JSON.stringify(testData, null, 2))

      const response = await apiClient.post('/api/test-connection', testData)
      console.log('Raw API response received:', response)
      console.log('Response status:', response.status)
      console.log('Response headers:', response.headers)
      
      const result = response.data
      console.log('Parsed response data:', result)
      console.log('Response body:', result.body)
      console.log('Response success:', result.success)
      console.log('Response status from data:', result.status)
      console.log('Response message:', result.message)
      
      // Determine success based on status code (2xx) or explicit success flag
      const isSuccess = result.success === true || (result.status >= 200 && result.status < 300)
      console.log('Calculated isSuccess:', isSuccess)
      
      setTestResult({
        success: isSuccess,
        message: isSuccess ? (result.message || 'Connection successful') : (result.error || result.message || 'Connection failed'),
        status: result.status,
        statusText: result.statusText,
        timestamp: new Date()
      })
      
      console.log('Test result set to:', {
        success: isSuccess,
        message: isSuccess ? (result.message || 'Connection successful') : (result.error || result.message || 'Connection failed'),
        status: result.status,
        statusText: result.statusText
      })
      
      // Also show an alert for immediate feedback
      alert(`Test Result: ${isSuccess ? 'SUCCESS' : 'FAILED'}\nStatus: ${result.status}\nMessage: ${result.message || 'No message'}`)
    } catch (err) {
      setTestResult({
        success: false,
        message: err instanceof Error ? err.message : 'Test failed: Unknown error',
        timestamp: new Date()
      })
    } finally {
      setTestingConnection(false)
    }
  }

  const handleRunNow = async () => {
    if (!connection) return
    try {
      // Chuyển hướng đến trang starting với connectionId
      router.push(`/runs/starting?connectionId=${connection.id}`)
    } catch (err) {
      alert('Run failed: ' + (err.response?.data?.message || err.message || err))
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-muted rounded w-1/4 mb-4"></div>
            <div className="h-64 bg-muted rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !connection) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center gap-4 mb-6">
            <Link href="/connections">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Connections
              </Button>
            </Link>
          </div>
          <Card className="border-destructive">
            <CardHeader>
              <CardTitle className="text-destructive">Connection Not Found</CardTitle>
              <CardDescription>
                The connection you're looking for doesn't exist or has been deleted.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Error: {error || 'Unknown error'}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center gap-2 mb-6">
          <BackToHomeButton />
          <span className="text-muted-foreground">/</span>
          <Link href="/connections">
            <Button variant="ghost" size="sm" className="h-auto p-0 text-muted-foreground hover:text-foreground">
              Connections
            </Button>
          </Link>
          <span className="text-muted-foreground">/</span>
          <span className="text-sm font-medium">{connection.name}</span>
        </div>

        {/* Header Section */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 mb-8">
          <div className="space-y-2">
            <h1 className="text-4xl font-bold tracking-tight">{connection.name}</h1>
            <p className="text-lg text-muted-foreground">{connection.description}</p>
            <div className="flex items-center gap-4">
              <Badge variant={connection.isActive ? "default" : "secondary"} className="text-sm">
                {connection.isActive ? "Active" : "Inactive"}
              </Badge>
              <span className="text-sm text-muted-foreground">
                Created {new Date(connection.createdAt).toLocaleDateString()}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button 
              variant="outline" 
              size="default"
              onClick={handleTestConnection}
              disabled={testingConnection}
              className="flex items-center gap-2"
            >
              {testingConnection ? (
                <Clock className="h-4 w-4 animate-spin" />
              ) : (
                <Activity className="h-4 w-4" />
              )}
              {testingConnection ? 'Testing...' : 'Test Connection'}
            </Button>
            <Button 
              size="default"
              onClick={handleRunNow}
              disabled={!connection.isActive}
              className="flex items-center gap-2"
            >
              <Play className="h-4 w-4" />
              Run Now
            </Button>
            <Link href={`/connections/${connection.id}/edit`}>
              <Button variant="outline" size="default" className="flex items-center gap-2">
                <Edit className="h-4 w-4" />
                Edit
              </Button>
            </Link>
          </div>
        </div>

        {/* Test Result Alert */}
        {testResult && (
          <Card className={`mb-8 border-l-4 ${testResult.success ? 'border-l-green-500 bg-green-50/50' : 'border-l-red-500 bg-red-50/50'}`}>
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                {testResult.success ? (
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
                )}
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className={`font-semibold ${testResult.success ? 'text-green-800' : 'text-red-800'}`}>
                      Connection Test {testResult.success ? 'Successful' : 'Failed'}
                    </h3>
                    <span className="text-xs text-muted-foreground">
                      {testResult.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <p className={`text-sm mt-1 ${testResult.success ? 'text-green-700' : 'text-red-700'}`}>
                    {testResult.message}
                  </p>
                  {testResult.status && (
                    <p className="text-xs text-muted-foreground mt-2">
                      HTTP {testResult.status} {testResult.statusText}
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid gap-8 lg:grid-cols-12">
          {/* Main Content - Configuration and Recent Runs */}
          <div className="lg:col-span-8 space-y-8">
            {/* Configuration */}
            <Card className="shadow-sm">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-3 text-xl">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <Settings className="h-5 w-5 text-primary" />
                  </div>
                  Configuration
                </CardTitle>
                <CardDescription>
                  API endpoint configuration and authentication settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Base URL and Method */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-foreground">Base URL</label>
                    <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg border">
                      <code className="text-sm font-mono flex-1 break-all">
                        {connection.baseUrl}
                      </code>
                      <Button variant="ghost" size="sm" className="shrink-0">
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-foreground">Method</label>
                    <div className="p-3 bg-muted/50 rounded-lg border">
                      <Badge variant="outline" className="font-mono text-sm">
                        {connection.method}
                      </Badge>
                    </div>
                  </div>
                </div>

                {/* Authentication and Status */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-foreground">Authentication</label>
                    <div className="p-3 bg-muted/50 rounded-lg border">
                      <Badge variant="secondary" className="text-sm">
                        {connection.authType || 'None'}
                      </Badge>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-foreground">Status</label>
                    <div className="p-3 bg-muted/50 rounded-lg border">
                      <Badge variant={connection.isActive ? "default" : "secondary"} className="text-sm">
                        {connection.isActive ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                  </div>
                </div>

                {/* Headers */}
                {connection.headers && Array.isArray(connection.headers) && connection.headers.length > 0 && (
                  <div className="space-y-3">
                    <label className="text-sm font-semibold text-foreground">Headers</label>
                    <div className="space-y-2">
                      {connection.headers.map((header, index) => {
                        console.log('Header', index, ':', header, 'Type:', typeof header, 'Keys:', Object.keys(header))
                        
                        // Simplified header display logic
                        let displayKey = '', displayValue = ''
                        
                        if (typeof header === 'object' && header !== null) {
                          if (Object.keys(header).length === 0) {
                            // Empty object
                            displayKey = '(empty header)'
                            displayValue = '(empty value)'
                          } else if (header.key && header.value !== undefined) {
                            // Format: {key: "name", value: "val"}
                            displayKey = header.key
                            displayValue = String(header.value || '')
                          } else if (Object.keys(header).length === 1) {
                            // Format: {"X-API-Key": "value"}
                            const [key, value] = Object.entries(header)[0]
                            displayKey = key
                            displayValue = String(value || '')
                          } else {
                            // Complex object - show as raw
                            displayKey = `Object with ${Object.keys(header).length} keys`
                            displayValue = JSON.stringify(header)
                          }
                        } else if (typeof header === 'string') {
                          // String format - try to parse as "Key: Value"
                          const colonIndex = header.indexOf(':')
                          if (colonIndex > 0) {
                            displayKey = header.substring(0, colonIndex).trim()
                            displayValue = header.substring(colonIndex + 1).trim()
                          } else {
                            displayKey = header
                            displayValue = ''
                          }
                        } else {
                          // Other types
                          displayKey = `Unknown type: ${typeof header}`
                          displayValue = String(header)
                        }
                        
                        return (
                          <div key={index} className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg border">
                            <code className="text-sm font-mono bg-background px-2 py-1 rounded border shrink-0">
                              {displayKey}
                            </code>
                            <span className="text-muted-foreground">→</span>
                            <code className="text-sm font-mono bg-background px-2 py-1 rounded border flex-1 min-w-0">
                              {displayValue.length > 60 ? displayValue.substring(0, 60) + '...' : displayValue}
                            </code>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Runs */}
            <Card className="shadow-sm">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-3 text-xl">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <Clock className="h-5 w-5 text-primary" />
                  </div>
                  Recent Runs
                </CardTitle>
                <CardDescription>
                  Latest pipeline executions for this connection
                </CardDescription>
              </CardHeader>
              <CardContent>
                {runs.length > 0 ? (
                  <div className="space-y-4">
                    {runs.map((run) => (
                      <div 
                        key={run.id}
                        className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-center gap-4">
                          <div className="flex-shrink-0">
                            {(run.status === 'completed' || run.status === 'success') && (
                              <div className="p-2 bg-green-100 rounded-full">
                                <CheckCircle className="h-4 w-4 text-green-600" />
                              </div>
                            )}
                            {run.status === 'failed' && (
                              <div className="p-2 bg-red-100 rounded-full">
                                <XCircle className="h-4 w-4 text-red-600" />
                              </div>
                            )}
                            {run.status === 'running' && (
                              <div className="p-2 bg-blue-100 rounded-full">
                                <Activity className="h-4 w-4 text-blue-600 animate-spin" />
                              </div>
                            )}
                          </div>
                          <div>
                            <p className="font-medium">Run {String(run.id).substring(0, 8)}</p>
                            <p className="text-sm text-muted-foreground">
                              {new Date(run.startedAt).toLocaleString()}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          {run.recordsExtracted && (
                            <p className="font-medium text-lg">{run.recordsExtracted.toLocaleString()}</p>
                          )}
                          {run.duration && (
                            <p className="text-sm text-muted-foreground">
                              {Math.round(run.duration / 1000)}s
                            </p>
                          )}
                          {run.errorMessage && (
                            <p className="text-sm text-red-500 max-w-xs truncate">
                              {String(run.errorMessage).substring(0, 50)}...
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="p-4 bg-muted/50 rounded-full w-fit mx-auto mb-4">
                      <Clock className="h-8 w-8 text-muted-foreground" />
                    </div>
                    <h3 className="font-medium text-lg mb-2">No runs yet</h3>
                    <p className="text-muted-foreground mb-4">Click "Run Now" to execute this connection</p>
                    <Button 
                      onClick={handleRunNow}
                      disabled={!connection.isActive}
                      className="flex items-center gap-2"
                    >
                      <Play className="h-4 w-4" />
                      Run Now
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Statistics and Quick Actions */}
          <div className="lg:col-span-4 space-y-6">
            {/* Statistics */}
            <Card className="shadow-sm">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-3 text-xl">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <Database className="h-5 w-5 text-primary" />
                  </div>
                  Statistics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">Total Runs</span>
                    <span className="text-2xl font-bold">{connection.totalRuns || 0}</span>
                  </div>
                </div>
                
                <Separator />
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">Success Rate</span>
                    <span className="text-lg font-semibold">{connection.successRate || 0}%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-3">
                    <div 
                      className="bg-gradient-to-r from-green-500 to-green-600 h-3 rounded-full transition-all duration-500"
                      style={{ width: `${connection.successRate || 0}%` }}
                    />
                  </div>
                </div>
                
                <Separator />
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">Last Run</span>
                    <span className="text-sm font-medium">
                      {connection.lastRun ? new Date(connection.lastRun).toLocaleDateString() : 'Never'}
                    </span>
                  </div>
                </div>
                
                <Separator />
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">Created</span>
                    <span className="text-sm font-medium">
                      {new Date(connection.createdAt).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card className="shadow-sm">
              <CardHeader className="pb-4">
                <CardTitle className="text-xl">Quick Actions</CardTitle>
                <CardDescription>
                  Manage your connection settings and data
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Link href={`/mappings?connectionId=${connection.id}`}>
                  <Button variant="outline" className="w-full justify-start h-12 text-left">
                    <div className="p-2 bg-blue-100 rounded-lg mr-3">
                      <Settings className="h-4 w-4 text-blue-600" />
                    </div>
                    <div>
                      <div className="font-medium">Field Mappings</div>
                      <div className="text-xs text-muted-foreground">Configure data transformations</div>
                    </div>
                  </Button>
                </Link>
                
                <Link href={`/schedules?connectionId=${connection.id}`}>
                  <Button variant="outline" className="w-full justify-start h-12 text-left">
                    <div className="p-2 bg-green-100 rounded-lg mr-3">
                      <Clock className="h-4 w-4 text-green-600" />
                    </div>
                    <div>
                      <div className="font-medium">Schedules</div>
                      <div className="text-xs text-muted-foreground">Set up automated runs</div>
                    </div>
                  </Button>
                </Link>
                
                <Link href={`/runs?connectionId=${connection.id}`}>
                  <Button variant="outline" className="w-full justify-start h-12 text-left">
                    <div className="p-2 bg-purple-100 rounded-lg mr-3">
                      <Activity className="h-4 w-4 text-purple-600" />
                    </div>
                    <div>
                      <div className="font-medium">All Runs</div>
                      <div className="text-xs text-muted-foreground">View execution history</div>
                    </div>
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
