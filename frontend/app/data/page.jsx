"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Database, Search, Filter, Clock, XCircle, ChevronDown, Download, BarChart3, RotateCcw } from "lucide-react"
import { PageLayout } from "@/components/ui/page-layout"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import apiClient from "../../services/apiClient.js"
import { AdvancedFilterPanel } from "@/components/data-explorer/advanced-filter-panel.jsx"
import { DataExportDialog } from "@/components/data-explorer/data-export-dialog.jsx"

export default function DataPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedConnection, setSelectedConnection] = useState("all")
  const [filters, setFilters] = useState({})
  const [filteredData, setFilteredData] = useState(null)
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)

  useEffect(() => {
    setLoading(true)
    console.log('[DataPage] Fetching data from /api/data...')
    apiClient
      .get("/api/data")
      .then((response) => {
        console.log('[DataPage] SUCCESS - Full Axios Response received:', response)
        console.log('[DataPage] Response status:', response.status)
        console.log('[DataPage] Response data type:', typeof response.data)
        console.log('[DataPage] Response data:', response.data)
        
        // Axios wraps the server response in response.data
        const apiData = response.data
        
        console.log('[DataPage] Checking data structure...')
        console.log('[DataPage] Has summary:', !!apiData?.summary)
        console.log('[DataPage] Has connectionBreakdown:', !!apiData?.connectionBreakdown)
        console.log('[DataPage] Summary content:', apiData?.summary)
        
        if (apiData && typeof apiData === 'object' && apiData.summary && apiData.connectionBreakdown) {
          console.log('[DataPage] ✅ Valid data received, setting state')
          setData(apiData)
          setFilteredData(apiData)
          setError(null)
          setLoading(false)
        } else {
          console.warn('[DataPage] ❌ Invalid data structure:')
          console.warn('  - apiData is object:', typeof apiData === 'object')
          console.warn('  - has summary:', !!apiData?.summary)
          console.warn('  - has connectionBreakdown:', !!apiData?.connectionBreakdown)
          console.warn('  - full data:', apiData)
          setError("Invalid data format from server")
          setLoading(false)
        }
      })
      .catch((err) => {
        console.error('[DataPage] ❌ FAILED to fetch data')
        console.error('[DataPage] Error:', err)
        console.error('[DataPage] Error response status:', err.response?.status)
        console.error('[DataPage] Error response data:', err.response?.data)
        console.error('[DataPage] Error message:', err.message)
        const errorMsg = err.response?.data?.error || err.message || 'Unknown error'
        setError("Failed to load data: " + errorMsg)
        setLoading(false)
      })
  }, [])

  useEffect(() => {
    if (!data) return

    const result = { ...data }

    // Filter by connection
    if (selectedConnection !== "all") {
      result.connectionBreakdown = result.connectionBreakdown.filter((c) => c.connectionId === selectedConnection)
    }

    // Filter by search term
    if (searchTerm) {
      result.connectionBreakdown = result.connectionBreakdown.filter(
        (c) =>
          (c.connectionName || c.connectionId).toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.connectionId.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.description?.toLowerCase().includes(searchTerm.toLowerCase()),
      )
    }

    // Apply advanced filters
    if (Object.keys(filters).length > 0) {
      result.connectionBreakdown = result.connectionBreakdown.filter((connection) => {
        if (filters.minRecords && connection.totalRecords < filters.minRecords) return false
        if (filters.maxRecords && connection.totalRecords > filters.maxRecords) return false
        if (filters.minExecutionTime && connection.avgExecutionTime < filters.minExecutionTime) return false
        if (filters.maxExecutionTime && connection.avgExecutionTime > filters.maxExecutionTime) return false
        if (filters.status && connection.status !== filters.status) return false
        return true
      })
    }

    setFilteredData(result)
  }, [data, searchTerm, selectedConnection, filters])

  const connections = data?.connectionBreakdown?.map((c) => c.connectionId) || []
  const uniqueConnections = [...new Set(connections)]

  return (
    <div suppressHydrationWarning>
      <PageLayout title="Data Explorer" description="Browse and export extracted data" showBackButton={true} icon={<div className="p-2 bg-gradient-to-br from-orange-100 to-orange-50 rounded-lg"><Database className="h-6 w-6 text-orange-600" /></div>}>
        <Card className="mb-6 bg-gradient-to-r from-slate-50 to-slate-100 border">
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex flex-col lg:flex-row gap-4">
                <div className="flex-1 min-w-0 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <Input
                    placeholder="Search by connection name or ID..."
                    className="pl-10 pr-4"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <Select value={selectedConnection} onValueChange={setSelectedConnection}>
                  <SelectTrigger className="w-full sm:w-48">
                    <Filter className="h-4 w-4 mr-2 flex-shrink-0" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Connections</SelectItem>
                    {uniqueConnections.map((conn) => (
                      <SelectItem key={conn} value={conn}>
                        {conn}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Collapsible open={showAdvancedFilters} onOpenChange={setShowAdvancedFilters}>
                <CollapsibleTrigger asChild>
                  <Button variant="outline" className="w-full justify-between">
                    <span className="flex items-center gap-2">
                      <Filter className="h-4 w-4" />
                      Advanced Filters
                    </span>
                    <ChevronDown className="h-4 w-4" />
                  </Button>
                </CollapsibleTrigger>
                <CollapsibleContent className="mt-4">
                  <AdvancedFilterPanel filters={filters} onFiltersChange={setFilters} />
                </CollapsibleContent>
              </Collapsible>
            </div>
          </CardContent>
        </Card>

      {loading ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Clock className="h-12 w-12 text-muted-foreground mb-4 animate-spin" />
            <p className="text-muted-foreground">Loading data...</p>
          </CardContent>
        </Card>
      ) : error ? (
        <Card className="border-destructive">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <XCircle className="h-12 w-12 text-destructive mb-4" />
            <h3 className="text-lg font-semibold mb-2">Error loading data</h3>
            <p className="text-muted-foreground text-center">{error}</p>
          </CardContent>
        </Card>
      ) : !filteredData || (filteredData.connectionBreakdown || []).length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Database className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No data yet</h3>
            <p className="text-muted-foreground text-center mb-4 text-pretty max-w-md">
              Data will appear here once you run an API connection
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-4 grid-cols-2 lg:grid-cols-4 mb-6">
            <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <RotateCcw className="h-4 w-4 text-blue-600" />
                  <CardDescription className="text-blue-700">Total Runs</CardDescription>
                </div>
                <CardTitle className="text-2xl lg:text-3xl text-blue-900">{filteredData.summary.totalRuns}</CardTitle>
              </CardHeader>
            </Card>
            <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-purple-600" />
                  <CardDescription className="text-purple-700">Total Records</CardDescription>
                </div>
                <CardTitle className="text-2xl lg:text-3xl text-purple-900">{filteredData.summary.totalRecords}</CardTitle>
              </CardHeader>
            </Card>
            <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-green-600" />
                  <CardDescription className="text-green-700">Avg Time</CardDescription>
                </div>
                <CardTitle className="text-2xl lg:text-3xl text-green-900">{Math.round(filteredData.summary.avgExecutionTime / 1000)}s</CardTitle>
              </CardHeader>
            </Card>
            <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-orange-600" />
                  <CardDescription className="text-orange-700">Data Size</CardDescription>
                </div>
                <CardTitle className="text-2xl lg:text-3xl text-orange-900">{filteredData.summary.estimatedDataSize}</CardTitle>
              </CardHeader>
            </Card>
          </div>

          <div className="grid gap-4">
            {filteredData.connectionBreakdown.map((connection) => {
              const lastRun = new Date(connection.lastRun)
              return (
                <Card key={connection.connectionId} className="group hover:shadow-lg transition-all duration-200 border-l-4 border-l-blue-500 hover:border-l-purple-500 overflow-hidden">
                  <CardHeader className="pb-3">
                    <div className="flex flex-col gap-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 mb-2 flex-wrap">
                            <Database className="h-5 w-5 text-blue-600 flex-shrink-0" />
                            <CardTitle className="text-lg truncate group-hover:text-blue-600 transition-colors">
                              {connection.connectionName || connection.connectionId}
                            </CardTitle>
                            <div className="flex gap-2 flex-wrap">
                              <Badge variant="outline" className="flex-shrink-0">
                                <Database className="h-3 w-3 mr-1" />
                                {connection.totalRecords}
                              </Badge>
                              <Badge variant="secondary" className="flex-shrink-0">
                                <RotateCcw className="h-3 w-3 mr-1" />
                                {connection.runCount}
                              </Badge>
                            </div>
                          </div>
                          <CardDescription className="line-clamp-1">
                            Last updated: {lastRun.toLocaleString()} • Avg: {Math.round(connection.avgExecutionTime / 1000)}s
                          </CardDescription>
                        </div>
                        <div className="flex-shrink-0">
                          <DataExportDialog connection={connection} />
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                </Card>
              )
            })}
          </div>
        </>
      )}
    </PageLayout>
    </div>
  )
}
