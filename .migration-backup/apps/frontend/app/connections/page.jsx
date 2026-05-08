'use client'

import { useEffect, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Plus, Database, Calendar, Activity, Clock, XCircle, Trash2, Search, Filter, Zap, Globe, Key, Settings, Eye, Edit, ArrowUpDown, ChevronLeft, ChevronRight } from "lucide-react"
import { PageLayout } from "@/components/ui/page-layout"
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog"
import apiClient from "../../services/apiClient.js"

export default function ConnectionsPage() {
  const [connections, setConnections] = useState([])
  const [filteredConnections, setFilteredConnections] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deletingId, setDeletingId] = useState(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [filterStatus, setFilterStatus] = useState("all")
  const [sortBy, setSortBy] = useState("name")
  const [sortOrder, setSortOrder] = useState("asc")
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 12

  const loadConnections = async () => {
    try {
      setLoading(true)
      setError(null) // Clear any previous errors
      const res = await apiClient.get('/api/connections')
      const data = res.data || []
      // Ensure data is always an array
      const connectionsArray = Array.isArray(data) ? data : []
      setConnections(connectionsArray)
      setFilteredConnections(connectionsArray)
    } catch (err) {
      console.error('[v0] Error fetching connections:', err)
      setError('Failed to load connections')
    } finally {
      setLoading(false)
    }
  }

  // Filter, sort and paginate connections
  useEffect(() => {
    let filtered = connections

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(conn =>
        conn.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        conn.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        getConnectionPreview(conn)?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Filter by status
    if (filterStatus !== "all") {
      filtered = filtered.filter(conn =>
        filterStatus === "active" ? conn.isActive : !conn.isActive
      )
    }

    // Sort connections
    filtered.sort((a, b) => {
      let aValue, bValue

      switch (sortBy) {
        case "name":
          aValue = a.name?.toLowerCase() || ""
          bValue = b.name?.toLowerCase() || ""
          break
        case "created":
          aValue = new Date(a.createdAt || 0)
          bValue = new Date(b.createdAt || 0)
          break
        case "lastUsed":
          aValue = new Date(a.lastUsedAt || 0)
          bValue = new Date(b.lastUsedAt || 0)
          break
        default:
          aValue = a.name?.toLowerCase() || ""
          bValue = b.name?.toLowerCase() || ""
      }

      if (aValue < bValue) return sortOrder === "asc" ? -1 : 1
      if (aValue > bValue) return sortOrder === "asc" ? 1 : -1
      return 0
    })

    setFilteredConnections(filtered)
    setCurrentPage(1) // Reset to first page when filters change
  }, [connections, searchTerm, filterStatus, sortBy, sortOrder])

  // Get paginated connections
  const paginatedConnections = filteredConnections.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )

  const totalPages = Math.ceil(filteredConnections.length / itemsPerPage)

  // Helper function to get connection preview
  const getConnectionPreview = (conn) => {
    if (conn.description && conn.description !== 'No description provided') {
      return conn.description
    }

    // Try to extract method and endpoint from various fields
    let preview = ''
    if (conn.baseUrl && conn.endpoint) {
      preview = `${conn.method || 'GET'} ${conn.baseUrl}${conn.endpoint}`
    } else if (conn.baseUrl) {
      preview = `${conn.method || 'GET'} ${conn.baseUrl}`
    } else if (conn.endpoint) {
      preview = `${conn.method || 'GET'} ${conn.endpoint}`
    }

    // Look for URL in description or other fields
    if (!preview) {
      const urlMatch = conn.description?.match(/https?:\/\/[^\s]+/)
      if (urlMatch) {
        preview = `${conn.method || 'GET'} ${urlMatch[0]}`
      }
    }

    // Truncate long URLs for better display
    if (preview && preview.length > 80) {
      const method = preview.split(' ')[0]
      const url = preview.substring(preview.indexOf(' ') + 1)
      const truncatedUrl = url.length > 60 ? url.substring(0, 60) + '...' : url
      return `${method} ${truncatedUrl}`
    }

    return preview || null
  }

  const toggleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    } else {
      setSortBy(field)
      setSortOrder("asc")
    }
  }

  useEffect(() => {
    loadConnections()
  }, [])

  const deleteConnection = async (connectionId) => {
    setDeletingId(connectionId)
    setError(null) // Clear any previous errors
    
    // Optimistic update: remove from UI immediately
    const previousConnections = [...connections]
    setConnections(connections.filter(conn => conn.id !== connectionId))
    
    try {
      const res = await apiClient.delete(`/api/connections/${connectionId}`)
      // Check if response is successful (status 2xx or has ok: true)
      if (res.status >= 200 && res.status < 300 && (!res.data || res.data.ok !== false)) {
        // Success - connection already removed from UI
      } else {
        // Revert optimistic update on failure
        setConnections(previousConnections)
        throw new Error('Failed to delete connection')
      }
    } catch (err) {
      // Revert optimistic update on error
      setConnections(previousConnections)
      console.error('[v0] Error deleting connection:', err)
      setError(err instanceof Error ? err.message : 'Failed to delete connection')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <PageLayout
      title="API Connections"
      description="Manage your API integrations and configurations"
      showBackButton={true}
      icon={<div className="p-2 bg-gradient-to-br from-blue-100 to-blue-50 rounded-lg"><Zap className="h-6 w-6 text-blue-600" /></div>}
      headerActions={
        <Link href="/connections/new">
          <Button className="w-full sm:w-auto gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-md hover:shadow-lg transition-all">
            <Plus className="h-4 w-4" />
            <span className="hidden sm:inline">New Connection</span>
            <span className="sm:hidden">New</span>
          </Button>
        </Link>
      }
    >
      {/* Search and Filter Bar */}
      {!loading && !error && connections.length > 0 && (
        <div className="flex flex-col lg:flex-row gap-4 mb-6 p-4 bg-gradient-to-r from-slate-50 to-slate-100 rounded-lg border border-slate-200">
          <div className="relative flex-1 min-w-0">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground flex-shrink-0" />
            <Input
              placeholder="Search connections..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 bg-white border-slate-200"
            />
          </div>
          <div className="flex flex-wrap gap-2 justify-center lg:justify-start">
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-full sm:w-40 bg-white border-slate-200">
                <ArrowUpDown className="h-4 w-4 mr-2 flex-shrink-0" />
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name">Name {sortBy === "name" && (sortOrder === "asc" ? "↑" : "↓")}</SelectItem>
                <SelectItem value="created">Date Created {sortBy === "created" && (sortOrder === "asc" ? "↑" : "↓")}</SelectItem>
                <SelectItem value="lastUsed">Last Used {sortBy === "lastUsed" && (sortOrder === "asc" ? "↑" : "↓")}</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              size="sm"
              onClick={() => toggleSort(sortBy)}
              className="gap-2 flex-shrink-0 border-slate-200 hover:bg-white"
            >
              <ArrowUpDown className="h-4 w-4" />
              {sortOrder === "asc" ? "↑" : "↓"}
            </Button>
            <Button
              variant={filterStatus === "all" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilterStatus("all")}
              className="gap-2 flex-shrink-0"
            >
              <Filter className="h-4 w-4" />
              <span className="hidden sm:inline">All ({connections.length})</span>
              <span className="sm:hidden">{connections.length}</span>
            </Button>
            <Button
              variant={filterStatus === "active" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilterStatus("active")}
              className="gap-2 flex-shrink-0"
            >
              <Zap className="h-4 w-4" />
              <span className="hidden sm:inline">Active ({connections.filter(c => c.isActive).length})</span>
              <span className="sm:hidden">{connections.filter(c => c.isActive).length}</span>
            </Button>
            <Button
              variant={filterStatus === "inactive" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilterStatus("inactive")}
              className="gap-2 flex-shrink-0"
            >
              <XCircle className="h-4 w-4" />
              <span className="hidden sm:inline">Inactive ({connections.filter(c => !c.isActive).length})</span>
              <span className="sm:hidden">{connections.filter(c => !c.isActive).length}</span>
            </Button>
          </div>
        </div>
      )}

      {loading ? (
        <Card className="bg-gradient-to-br from-white to-slate-50/50 border-slate-200">
          <CardContent className="flex flex-col items-center justify-center py-16" suppressHydrationWarning={true}>
            <div className="inline-block animate-spin mb-4">
              <Zap className="h-8 w-8 text-blue-500" />
            </div>
            <p className="text-muted-foreground">Loading connections...</p>
          </CardContent>
        </Card>
      ) : error ? (
        <Card className="border-red-200 bg-gradient-to-br from-red-50 to-red-100/50">
          <CardContent className="flex flex-col items-center justify-center py-16" suppressHydrationWarning={true}>
            <div className="flex items-center justify-center w-12 h-12 rounded-full bg-red-100 mb-4">
              <XCircle className="h-6 w-6 text-red-600" />
            </div>
            <h3 className="text-lg font-semibold text-red-900 mb-2">Error loading connections</h3>
            <p className="text-red-700 text-center mb-6 max-w-md">{error}</p>
            <Button onClick={loadConnections} variant="outline" className="border-red-300 hover:bg-red-50">
              Try Again
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
          {filteredConnections.length === 0 ? (
            <div className="col-span-full">
              <Card className="border-dashed border-2 border-slate-200 bg-gradient-to-br from-slate-50 to-slate-100/50">
                <CardContent className="flex flex-col items-center justify-center py-16">
                  <div className="flex items-center justify-center w-16 h-16 rounded-full bg-slate-200/50 mb-4">
                    <Database className="h-8 w-8 text-slate-500" />
                  </div>
                  <h3 className="text-xl font-semibold text-slate-900 mb-2">
                    {searchTerm || filterStatus !== "all" ? "No connections match your filters" : "No connections found"}
                  </h3>
                  <p className="text-slate-600 text-center mb-6 max-w-md">
                    {searchTerm || filterStatus !== "all"
                      ? "Try adjusting your search or filter criteria"
                      : "Create your first API connection to get started with data integration"
                    }
                  </p>
                  {(!searchTerm && filterStatus === "all") && (
                    <Link href="/connections/new" className="w-full sm:w-auto">
                      <Button className="w-full gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-md hover:shadow-lg transition-all">
                        <Plus className="h-4 w-4" />
                        Create Your First Connection
                      </Button>
                    </Link>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            paginatedConnections.map((conn) => (
              <Card key={conn.id} className="group bg-gradient-to-br from-white to-slate-50/50 hover:shadow-lg transition-all duration-200 border-l-4 border-l-blue-500 hover:border-l-purple-500 border-slate-200 overflow-hidden">
                <CardHeader className="pb-3">
                  <div className="flex flex-col gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="p-2 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg flex-shrink-0">
                        <Globe className="h-5 w-5 text-blue-600" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <CardTitle className="text-lg truncate group-hover:text-blue-600 transition-colors text-slate-900">
                          {conn.name}
                        </CardTitle>
                      </div>
                    </div>
                    <CardDescription className="line-clamp-2 break-words ml-11 text-slate-600">
                      {getConnectionPreview(conn) || conn.description || 'No description provided'}
                    </CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                    <div className="flex items-center gap-2 flex-wrap flex-1">
                      <Link href={`/connections/${conn.id}`} className="flex-1 sm:flex-initial">
                        <Button variant="outline" size="sm" className="w-full sm:w-auto gap-2 hover:bg-blue-50 hover:border-blue-200 border-slate-200">
                          <Eye className="h-3 w-3" />
                          <span className="hidden sm:inline">View</span>
                        </Button>
                      </Link>
                      <Link href={`/connections/${conn.id}/edit`} className="flex-1 sm:flex-initial">
                        <Button variant="outline" size="sm" className="w-full sm:w-auto gap-2 hover:bg-purple-50 hover:border-purple-200 border-slate-200">
                          <Edit className="h-3 w-3" />
                          <span className="hidden sm:inline">Edit</span>
                        </Button>
                      </Link>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        className={`w-fit ${conn.isActive ? 'bg-green-100 text-green-800 hover:bg-green-200' : 'bg-gray-100 text-gray-800'}`}
                      >
                        {conn.isActive ? (
                          <>
                            <Zap className="h-3 w-3 mr-1 flex-shrink-0" />
                            <span className="hidden sm:inline">Active</span>
                          </>
                        ) : (
                          <>
                            <XCircle className="h-3 w-3 mr-1 flex-shrink-0" />
                            <span className="hidden sm:inline">Inactive</span>
                          </>
                        )}
                      </Badge>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-destructive hover:bg-destructive/10 hover:text-destructive flex-shrink-0"
                            disabled={deletingId === conn.id}
                          >
                            {deletingId === conn.id ? (
                              <Clock className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle className="flex items-center gap-2">
                              <Trash2 className="h-5 w-5 text-destructive" />
                              Delete Connection
                            </AlertDialogTitle>
                            <AlertDialogDescription>
                              Are you sure you want to delete "{conn.name}"? This action cannot be undone and will also remove all associated schedules and runs.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => deleteConnection(conn.id)}
                              className="bg-destructive hover:bg-destructive/90"
                            >
                              Delete Connection
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Pagination */}
      {!loading && !error && filteredConnections.length > 0 && totalPages > 1 && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-8 p-4 bg-gradient-to-r from-slate-50 to-slate-100 rounded-lg border border-slate-200">
          <div className="text-sm text-slate-600 text-center sm:text-left">
            Showing {Math.min((currentPage - 1) * itemsPerPage + 1, filteredConnections.length)} to {Math.min(currentPage * itemsPerPage, filteredConnections.length)} of {filteredConnections.length} connections
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="gap-1 sm:gap-2 border-slate-200 hover:bg-white"
            >
              <ChevronLeft className="h-4 w-4" />
              <span className="hidden sm:inline">Previous</span>
            </Button>

            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pageNum = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i
                if (pageNum > totalPages) return null
                return (
                  <Button
                    key={pageNum}
                    variant={pageNum === currentPage ? "default" : "outline"}
                    size="sm"
                    onClick={() => setCurrentPage(pageNum)}
                    className="w-8 h-8 p-0 sm:w-auto sm:h-9 sm:px-3"
                  >
                    <span className="sm:hidden">{pageNum}</span>
                    <span className="hidden sm:inline">{pageNum}</span>
                  </Button>
                )
              })}
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="gap-1 sm:gap-2 border-slate-200 hover:bg-white"
            >
              <span className="hidden sm:inline">Next</span>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </PageLayout>
  )
}
