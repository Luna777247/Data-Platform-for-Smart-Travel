'use client'

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Loader2, CheckCircle2, XCircle, ArrowLeft } from "lucide-react"
import Link from "next/link"
import { Progress } from "@/components/ui/progress"
import { BackToHomeButton } from "@/components/ui/back-to-home-button"
import apiClient from "../../../services/apiClient.js"

export default function RunStartingPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const connectionId = searchParams.get('connectionId')
  const [progress, setProgress] = useState(0)
  const [timeElapsed, setTimeElapsed] = useState(0)
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState(null)
  const [connection, setConnection] = useState(null)
  const [runId, setRunId] = useState(null)

  useEffect(() => {
    if (!connectionId) {
      setStatus('error')
      setError('No connection ID provided')
      return
    }

    let progressInterval

    const startRun = async () => {
      try {
        // Reset progress
        setProgress(0)
        setTimeElapsed(0)

        // Start progress timer
        progressInterval = setInterval(() => {
          setTimeElapsed(prev => {
            const newTime = prev + 1
            // Estimate progress based on time (rough estimate)
            const estimatedProgress = Math.min((newTime / 30) * 100, 90) // Max 90% until completion
            setProgress(estimatedProgress)
            return newTime
          })
        }, 1000)

        // Bước 1: Lấy thông tin connection
        setStatus('starting')
        setProgress(10)
        const connectionRes = await apiClient.get(`/api/connections/${connectionId}`)
        const connectionData = connectionRes.data
        setConnection(connectionData)
        setProgress(20)

        // Bước 2: Tạo run
        const headersObject = {}
        if (Array.isArray(connectionData.headers)) {
          connectionData.headers.forEach(header => {
            if (typeof header === 'object') {
              if (header.key && header.value) {
                headersObject[header.key] = header.value
              } else if (Object.keys(header).length === 1) {
                const [key, value] = Object.entries(header)[0]
                headersObject[key] = value
              }
            }
          })
        } else if (typeof connectionData.headers === 'object' && connectionData.headers !== null) {
          // Handle object format directly
          Object.assign(headersObject, connectionData.headers)
        }

        const runData = {
          connectionId: connectionData.connectionId || connectionData.id,
          apiConfig: {
            baseUrl: connectionData.baseUrl,
            method: connectionData.method,
            headers: headersObject,
            authType: connectionData.authType || 'none',
            authConfig: connectionData.authConfig || {}
          },
          parameters: connectionData.parameters || [],
          fieldMappings: []
        }

        setProgress(30)
        const response = await apiClient.post('/api/execute-run', runData)
        const result = response.data

        console.log('API Response:', response)
        console.log('Result data:', result)

        clearInterval(progressInterval)
        setProgress(100)

        if (result.runId) {
          setRunId(result.runId)
          setStatus('success')

          // Automatically redirect after 3 seconds
          setTimeout(() => {
            router.push(`/runs/${result.runId}`)
          }, 3000)
        } else {
          throw new Error('Failed to get run ID from response')
        }
      } catch (err) {
        console.error('Error starting run:', err)
        if (progressInterval) clearInterval(progressInterval)
        setStatus('error')
        setError(err.response?.data?.message || err.message || 'Failed to start pipeline')
        setProgress(0)
      }
    }

    startRun()

    // Cleanup function
    return () => {
      if (progressInterval) clearInterval(progressInterval)
    }
  }, [connectionId, router])

  const getStatusContent = () => {
    switch (status) {
      case 'starting':
        return {
          icon: <Loader2 className="h-12 w-12 text-blue-500 animate-spin" />,
          title: "Starting Pipeline",
          description: "Executing API call and processing data. This may take up to 30 seconds...",
          color: "text-blue-600"
        }
      case 'success':
        return {
          icon: <CheckCircle2 className="h-12 w-12 text-green-500" />,
          title: "Pipeline Started Successfully",
          description: `Run ID: ${runId}. Redirecting to run details...`,
          color: "text-green-600"
        }
      case 'error':
        return {
          icon: <XCircle className="h-12 w-12 text-red-500" />,
          title: "Failed to Start Pipeline",
          description: error || "An error occurred while starting the pipeline",
          color: "text-red-600"
        }
      default:
        return {
          icon: <Loader2 className="h-12 w-12 text-muted-foreground animate-spin" />,
          title: "Processing",
          description: "Please wait...",
          color: "text-muted-foreground"
        }
    }
  }

  const statusContent = getStatusContent()

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Navigation */}
        <div className="flex items-center gap-4 mb-8">
          <BackToHomeButton />
          <Button variant="ghost" asChild className="gap-2">
            <Link href="/connections">
              <ArrowLeft className="h-4 w-4" />
              Back to Connections
            </Link>
          </Button>
        </div>

        {/* Status Card */}
        <div className="max-w-2xl mx-auto">
          <Card className="shadow-lg">
            <CardHeader className="text-center pb-6">
              <div className="flex justify-center mb-4">
                {statusContent.icon}
              </div>
              <CardTitle className={`text-2xl ${statusContent.color}`}>
                {statusContent.title}
              </CardTitle>
              <CardDescription className="text-lg">
                {statusContent.description}
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-6">
              {/* Progress Bar - only show when starting */}
              {status === 'starting' && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>Progress</span>
                    <span>{Math.round(progress)}% • {timeElapsed}s elapsed</span>
                  </div>
                  <Progress value={progress} className="w-full" />
                  <p className="text-xs text-muted-foreground text-center">
                    This process may take up to 30 seconds depending on API response time
                  </p>
                </div>
              )}

              {/* Progress Steps */}
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${status === 'starting' || status === 'success' || status === 'error' ? 'bg-green-500' : 'bg-muted'}`} />
                  <span className={`text-sm ${status === 'starting' || status === 'success' || status === 'error' ? 'text-green-600 font-medium' : 'text-muted-foreground'}`}>
                    Initializing pipeline configuration
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${status === 'success' || status === 'error' ? 'bg-green-500' : status === 'starting' ? 'bg-blue-500 animate-pulse' : 'bg-muted'}`} />
                  <span className={`text-sm ${status === 'success' || status === 'error' ? 'text-green-600 font-medium' : status === 'starting' ? 'text-blue-600 font-medium' : 'text-muted-foreground'}`}>
                    Creating execution job
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${status === 'success' ? 'bg-green-500' : status === 'error' ? 'bg-red-500' : 'bg-muted'}`} />
                  <span className={`text-sm ${status === 'success' ? 'text-green-600 font-medium' : status === 'error' ? 'text-red-600 font-medium' : 'text-muted-foreground'}`}>
                    {status === 'success' ? 'Pipeline started successfully' : status === 'error' ? 'Pipeline failed to start' : 'Starting pipeline execution'}
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-center gap-4 pt-4">
                {status === 'error' && (
                  <Button asChild>
                    <Link href={`/connections/${connectionId}`}>
                      Try Again
                    </Link>
                  </Button>
                )}

                {status === 'success' && (
                  <Button asChild variant="outline">
                    <Link href={`/runs/${runId}`}>
                      View Run Details
                    </Link>
                  </Button>
                )}

                <Button variant="outline" asChild>
                  <Link href="/runs">
                    View All Runs
                  </Link>
                </Button>
              </div>

              {/* Auto-redirect notice */}
              {status === 'success' && (
                <p className="text-center text-sm text-muted-foreground">
                  You will be automatically redirected to the run details page in a few seconds...
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}