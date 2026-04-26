'use client'

import Link from "next/link"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Settings, Database, ArrowRight, Zap, Grid, Code, Type, Hash, Layers } from "lucide-react"
import { PageLayout } from "@/components/ui/page-layout"
import apiClient from "../../services/apiClient.js"

export default function MappingsPage() {
  const [mappings, setMappings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Function to get icon and color for data types
  const getTypeStyles = (dataType) => {
    const styles = {
      string: { icon: <Type className="h-3 w-3" />, bg: 'bg-blue-100', text: 'text-blue-800', label: 'bg-blue-50 border-blue-200' },
      number: { icon: <Hash className="h-3 w-3" />, bg: 'bg-green-100', text: 'text-green-800', label: 'bg-green-50 border-green-200' },
      array: { icon: <Layers className="h-3 w-3" />, bg: 'bg-purple-100', text: 'text-purple-800', label: 'bg-purple-50 border-purple-200' },
      boolean: { icon: <Grid className="h-3 w-3" />, bg: 'bg-orange-100', text: 'text-orange-800', label: 'bg-orange-50 border-orange-200' },
      object: { icon: <Code className="h-3 w-3" />, bg: 'bg-slate-100', text: 'text-slate-800', label: 'bg-slate-50 border-slate-200' },
    }
    return styles[dataType?.toLowerCase()] || styles['string']
  }

  useEffect(() => {
    async function fetchMappings() {
      try {
        console.log('Starting to fetch mappings...')
        setLoading(true)
        const response = await apiClient.get('/api/mappings')
        console.log('API Response:', response)
        const data = response?.data || {}
        console.log('Response data:', data)
        const mappings = data.mappings || []
        console.log('Mappings array:', mappings)
        setMappings(mappings)
        console.log('State updated with mappings')
      } catch (err) {
        console.error('Error fetching mappings:', err)
        setError(err instanceof Error ? err.message : 'Failed to load field mappings')
      } finally {
        setLoading(false)
      }
    }

    fetchMappings()
  }, [])

  if (loading) {
    return (
      <PageLayout
        title="Field Mappings"
        description="Configure how API fields map to database columns"
        showBackButton={false}
      >
        <div className="flex items-center justify-center py-16" suppressHydrationWarning={true}>
          <div className="text-center">
            <div className="inline-block animate-spin mb-4">
              <Zap className="h-8 w-8 text-blue-500" />
            </div>
            <p className="text-muted-foreground">Loading field mappings...</p>
          </div>
        </div>
      </PageLayout>
    )
  }

  if (error) {
    return (
      <PageLayout
        title="Field Mappings"
        description="Configure how API fields map to database columns"
        showBackButton={false}
      >
        <Card className="border-red-200 bg-gradient-to-br from-red-50 to-red-100/50">
          <CardContent className="flex flex-col items-center justify-center py-16" suppressHydrationWarning={true}>
            <div className="flex items-center justify-center w-12 h-12 rounded-full bg-red-100 mb-4">
              <span className="text-2xl">⚠️</span>
            </div>
            <h3 className="text-lg font-semibold text-red-900 mb-2">Error loading field mappings</h3>
            <p className="text-red-700 text-center mb-6 max-w-md">{error}</p>
            <Button onClick={() => window.location.reload()} variant="outline" className="border-red-300 hover:bg-red-50">
              Try Again
            </Button>
          </CardContent>
        </Card>
      </PageLayout>
    )
  }

  return (
    <PageLayout
      title="Field Mappings"
      description="Configure how API fields map to database columns"
      showBackButton={true}
      icon={<div className="p-2 bg-gradient-to-br from-indigo-100 to-indigo-50 rounded-lg"><ArrowRight className="h-6 w-6 text-indigo-600" /></div>}
    >

        {mappings.length === 0 ? (
          <Card className="border-dashed border-2 border-slate-200 bg-gradient-to-br from-slate-50 to-slate-100/50">
            <CardContent className="flex flex-col items-center justify-center py-16" suppressHydrationWarning={true}>
              <div className="flex items-center justify-center w-16 h-16 rounded-full bg-slate-200/50 mb-4">
                <Settings className="h-8 w-8 text-slate-500" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-2">No field mappings configured</h3>
              <p className="text-slate-600 text-center mb-6 text-pretty max-w-md">
                Create an API connection to configure field mappings and define how your API response fields map to database columns
              </p>
              <Link href="/connections/new">
                <Button className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white shadow-md hover:shadow-lg transition-all">
                  <Zap className="h-4 w-4 mr-2" />
                  Create Connection
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4" suppressHydrationWarning={true}>
            {mappings.map((mapping) => (
              <Card key={mapping.id} className="bg-gradient-to-br from-white to-slate-50/50 border-slate-200 hover:border-blue-300 hover:shadow-lg transition-all duration-300">
                <CardHeader>
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 mb-3 flex-wrap">
                        <CardTitle className="text-lg sm:text-xl font-semibold text-slate-900 truncate">{mapping.connectionName}</CardTitle>
                        <Badge className="w-fit bg-blue-100 text-blue-800 border-blue-200">
                          <Grid className="h-3 w-3 mr-1" />
                          {(mapping.fields || []).length} fields
                        </Badge>
                      </div>
                      <CardDescription className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2 text-xs sm:text-sm text-slate-600">
                        <span className="flex items-center gap-1">
                          <Database className="h-4 w-4 text-blue-600" />
                          Target table:
                        </span>
                        <code className="text-xs bg-slate-100 px-2 py-1 rounded font-mono text-slate-800">{mapping.tableName || 'N/A'}</code>
                        {mapping.lastUpdated && (
                          <span className="text-xs text-slate-500 mt-1 sm:mt-0 sm:ml-auto">
                            Updated {new Date(mapping.lastUpdated).toLocaleDateString()}
                          </span>
                        )}
                      </CardDescription>
                    </div>
                    <Link href={`/connections/${mapping.id}`} className="w-full sm:w-auto">
                      <Button variant="outline" size="sm" className="w-full sm:w-auto hover:bg-blue-50 border-slate-200">
                        Edit Mapping
                      </Button>
                    </Link>
                  </div>
                </CardHeader>
                <CardContent suppressHydrationWarning={true}>
                  <div className="space-y-2">
                    {(mapping.fields || []).map((field, index) => {
                      const typeStyles = getTypeStyles(field.dataType)
                      return (
                        <div key={index} className={`flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 p-3 rounded-lg border transition-all duration-200 ${typeStyles.label} hover:shadow-md group`}>
                          <div className="flex items-center gap-2 min-w-0 flex-1">
                            <code className="text-xs sm:text-sm text-slate-600 font-mono truncate flex-1 group-hover:text-slate-800">{field.sourcePath}</code>
                          </div>
                          <ArrowRight className="h-4 w-4 text-slate-400 flex-shrink-0 hidden sm:block" />
                          <div className="flex items-center gap-2 min-w-0 flex-1 sm:flex-initial">
                            <span className="font-medium text-slate-800 text-sm truncate">{field.targetField}</span>
                          </div>
                          <Badge className={`${typeStyles.bg} ${typeStyles.text} border-0 text-xs font-medium flex-shrink-0 flex items-center gap-1`}>
                            {typeStyles.icon}
                            {field.dataType}
                          </Badge>
                        </div>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
    </PageLayout>
  )
}
