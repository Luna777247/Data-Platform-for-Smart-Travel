'use client'

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Save, X, Plus, Trash2 } from "lucide-react"
import { toast } from "sonner"
import apiClient from "../../../../services/apiClient.js"

export default function EditConnectionPage() {
  const router = useRouter()
  const params = useParams()
  const id = Array.isArray(params?.id) ? params.id[0] : params?.id

  const [connection, setConnection] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    baseUrl: '',
    method: 'GET',
    authType: 'none',
    authConfig: {},
    isActive: true,
    headers: {},
    parameters: [],
    fieldMappings: [],
    tableName: ''
  })
  const [headerEntries, setHeaderEntries] = useState([])

  useEffect(() => {
    const fetchConnection = async () => {
      try {
        setLoading(true)
        const response = await apiClient.get(`/api/connections/${id}`)
        const connectionData = response.data
        setConnection(connectionData)
        setFormData({
          name: connectionData.name || '',
          description: connectionData.description || '',
          baseUrl: connectionData.baseUrl || '',
          method: connectionData.method || 'GET',
          authType: connectionData.authType || 'none',
          authConfig: connectionData.authConfig || {},
          isActive: connectionData.isActive ?? true,
          headers: connectionData.headers || {},
          parameters: connectionData.parameters || [],
          fieldMappings: connectionData.fieldMappings || [],
          tableName: connectionData.tableName || ''
        })
        if (connectionData.headers) {
          let headers = connectionData.headers;
          // If headers is array, convert to object
          if (Array.isArray(headers)) {
            const obj = {};
            headers.forEach(header => {
              if (header && typeof header === 'object') {
                // Try different formats
                let key, value;
                if (header.name && header.value) {
                  key = header.name;
                  value = header.value;
                } else if (header.key && header.value) {
                  key = header.key;
                  value = header.value;
                } else if (Object.keys(header).length === 1) {
                  key = Object.keys(header)[0];
                  value = header[key];
                }
                if (key && value) {
                  obj[key] = String(value);
                }
              }
            });
            headers = obj;
          }
          const entries = Object.entries(headers).map(([key, value]) => ({ key, value: String(value) }))
          setHeaderEntries(entries)
        }
      } catch (err) {
        console.error('[v0] Error fetching connection:', err)
        setError(err instanceof Error ? err.message : 'Failed to load connection')
      } finally {
        setLoading(false)
      }
    }
    if (id) fetchConnection()
  }, [id])

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }
  const handleAddHeader = () => setHeaderEntries(prev => [...prev, { key: '', value: '' }])
  const handleHeaderChange = (index, field, value) => setHeaderEntries(prev => prev.map((e, i) => i === index ? { ...e, [field]: value } : e))
  const handleRemoveHeader = (index) => setHeaderEntries(prev => prev.filter((_, i) => i !== index))

  const handleSave = async () => {
    if (!connection) return
    try {
      setSaving(true)
      setError(null)
      const headers = {}
      headerEntries.forEach(entry => {
        if (entry.key.trim() && entry.value.trim()) headers[entry.key.trim()] = entry.value.trim()
      })
      const updateData = { ...formData, headers }
      const res = await apiClient.put(`/api/connections/${connection.id}`, updateData)
      if (res.status < 200 || res.status >= 300) throw new Error('Failed to update connection')
      toast.success('Connection updated successfully!')
      router.push(`/connections/${connection.id}`)
    } catch (err) {
      console.error('[v0] Error updating connection:', err)
      setError(err instanceof Error ? err.message : 'Failed to update connection')
      toast.error('Failed to update connection')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading connection...</p>
          </div>
        </div>
      </div>
    )
  }
  if (error) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <p className="text-red-500 mb-4">{error}</p>
            <Link href="/connections">
              <Button variant="outline">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Connections
              </Button>
            </Link>
          </div>
        </div>
      </div>
    )
  }
  if (!connection) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <p className="text-muted-foreground mb-4">Connection not found</p>
            <Link href="/connections">
              <Button variant="outline">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Connections
              </Button>
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Link href={`/connections/${connection.id}`}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Edit Connection</h1>
            <p className="text-muted-foreground">{connection.name}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link href={`/connections/${connection.id}`}>
            <Button variant="outline" size="sm">
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
          </Link>
          <Button onClick={handleSave} disabled={saving} size="sm">
            <Save className="h-4 w-4 mr-2" />
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>

      {/* Form */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
            <CardDescription>Configure the basic connection settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="name">Name</Label>
              <Input id="name" value={formData.name} onChange={(e) => handleInputChange('name', e.target.value)} placeholder="Connection name" />
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea id="description" value={formData.description} onChange={(e) => handleInputChange('description', e.target.value)} placeholder="Connection description" rows={3} />
            </div>
            <div>
              <Label htmlFor="baseUrl">Base URL</Label>
              <Input id="baseUrl" type="url" value={formData.baseUrl} onChange={(e) => handleInputChange('baseUrl', e.target.value)} placeholder="https://api.example.com/v1" />
            </div>
            <div>
              <Label htmlFor="method">HTTP Method</Label>
              <Select value={formData.method} onValueChange={(value) => handleInputChange('method', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="GET">GET</SelectItem>
                  <SelectItem value="POST">POST</SelectItem>
                  <SelectItem value="PUT">PUT</SelectItem>
                  <SelectItem value="PATCH">PATCH</SelectItem>
                  <SelectItem value="DELETE">DELETE</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Authentication & Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Authentication & Settings</CardTitle>
            <CardDescription>Configure authentication and connection settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="authType">Authentication Type</Label>
              <Select value={formData.authType} onValueChange={(value) => handleInputChange('authType', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="api-key">API Key</SelectItem>
                  <SelectItem value="bearer">Bearer Token</SelectItem>
                  <SelectItem value="basic">Basic Auth</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Authentication Configuration */}
            {formData.authType === 'api-key' && (
              <div className="space-y-3 border-t pt-4">
                <h4 className="font-medium">API Key Configuration</h4>
                <div>
                  <Label htmlFor="keyName">Header Name</Label>
                  <Input
                    id="keyName"
                    value={formData.authConfig?.keyName || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      authConfig: { ...prev.authConfig, keyName: e.target.value }
                    }))}
                    placeholder="X-API-Key"
                  />
                </div>
                <div>
                  <Label htmlFor="keyValue">API Key Value</Label>
                  <Input
                    id="keyValue"
                    type="password"
                    value={formData.authConfig?.keyValue || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      authConfig: { ...prev.authConfig, keyValue: e.target.value }
                    }))}
                    placeholder="Enter your API key"
                  />
                </div>
              </div>
            )}

            {formData.authType === 'bearer' && (
              <div className="space-y-3 border-t pt-4">
                <h4 className="font-medium">Bearer Token Configuration</h4>
                <div>
                  <Label htmlFor="token">Bearer Token</Label>
                  <Input
                    id="token"
                    type="password"
                    value={formData.authConfig?.token || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      authConfig: { ...prev.authConfig, token: e.target.value }
                    }))}
                    placeholder="Enter your bearer token"
                  />
                </div>
              </div>
            )}

            {formData.authType === 'basic' && (
              <div className="space-y-3 border-t pt-4">
                <h4 className="font-medium">Basic Authentication</h4>
                <div>
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    value={formData.authConfig?.username || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      authConfig: { ...prev.authConfig, username: e.target.value }
                    }))}
                    placeholder="Enter username"
                  />
                </div>
                <div>
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={formData.authConfig?.password || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      authConfig: { ...prev.authConfig, password: e.target.value }
                    }))}
                    placeholder="Enter password"
                  />
                </div>
              </div>
            )}
            <div>
              <Label>Status</Label>
              <div className="flex items-center gap-2 mt-2">
                <input type="checkbox" id="isActive" checked={formData.isActive} onChange={(e) => handleInputChange('isActive', e.target.checked)} className="rounded" />
                <Label htmlFor="isActive" className="font-normal">Connection is active</Label>
              </div>
            </div>
            <div>
              <Label>Connection ID</Label>
              <div className="mt-2">
                <Badge variant="outline">{connection.id}</Badge>
              </div>
            </div>
            <div>
              <Label>Created</Label>
              <div className="mt-2">
                <p className="text-sm text-muted-foreground">{new Date(connection.createdAt).toLocaleDateString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Headers */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>HTTP Headers</CardTitle>
                <CardDescription>Configure custom headers for API requests</CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={handleAddHeader}>
                <Plus className="h-4 w-4 mr-2" />
                Add Header
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {headerEntries.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <p>No headers configured</p>
                  <Button variant="outline" size="sm" onClick={handleAddHeader} className="mt-2">
                    <Plus className="h-4 w-4 mr-2" />
                    Add First Header
                  </Button>
                </div>
              ) : (
                headerEntries.map((entry, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <Input placeholder="Header name (e.g., Authorization)" value={entry.key} onChange={(e) => handleHeaderChange(index, 'key', e.target.value)} className="flex-1" />
                    <Input placeholder="Header value" value={entry.value} onChange={(e) => handleHeaderChange(index, 'value', e.target.value)} className="flex-1" />
                    <Button variant="outline" size="icon" onClick={() => handleRemoveHeader(index)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
