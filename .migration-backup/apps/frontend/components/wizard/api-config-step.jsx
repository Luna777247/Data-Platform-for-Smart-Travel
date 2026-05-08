'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Plus, Trash2, Eye, EyeOff } from 'lucide-react'
import apiClient from '../../services/apiClient.js'

export function ApiConfigStep({ data, onChange }) {
  const [showAuthValue, setShowAuthValue] = useState(false)

  const updateField = (field, value) => {
    onChange({ ...data, [field]: value })
  }

  const addHeader = () => {
    onChange({
      ...data,
      headers: [...data.headers, { key: '', value: '' }],
    })
  }

  const updateHeader = (index, field, value) => {
    const newHeaders = [...data.headers]
    newHeaders[index][field] = value
    onChange({ ...data, headers: newHeaders })
  }

  const removeHeader = (index) => {
    onChange({
      ...data,
      headers: data.headers.filter((_, i) => i !== index),
    })
  }

  return (
    <div className="space-y-6">
      {/* Basic Information */}
      <div className="space-y-4">
        <div>
          <Label htmlFor="name">Connection Name *</Label>
          <Input
            id="name"
            placeholder="e.g., User Data API"
            value={data.name}
            onChange={(e) => updateField('name', e.target.value)}
            className="mt-1.5"
          />
        </div>

        <div>
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            placeholder="Brief description of what this API does"
            value={data.description}
            onChange={(e) => updateField('description', e.target.value)}
            className="mt-1.5"
            rows={3}
          />
        </div>
      </div>

      {/* API Endpoint */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold">API Endpoint</h3>
        <div className="grid gap-4 md:grid-cols-4">
          <div className="md:col-span-1">
            <Label htmlFor="method">Method</Label>
            <Select value={data.method} onValueChange={(value) => updateField('method', value)}>
              <SelectTrigger id="method" className="mt-1.5">
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
          <div className="md:col-span-3">
            <Label htmlFor="baseUrl">Base URL *</Label>
            <Input
              id="baseUrl"
              placeholder="https://api.example.com/v1/users"
              value={data.baseUrl}
              onChange={(e) => updateField('baseUrl', e.target.value)}
              className="mt-1.5"
            />
          </div>
        </div>
      </div>

      {/* Headers */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">Headers</h3>
          <Button type="button" variant="outline" size="sm" onClick={addHeader} className="gap-2 bg-transparent">
            <Plus className="h-3 w-3" />
            Add Header
          </Button>
        </div>
        {data.headers.length === 0 ? (
          <Card className="p-4 border-dashed">
            <p className="text-sm text-muted-foreground text-center">No headers added yet</p>
          </Card>
        ) : (
          <div className="space-y-2">
            {data.headers.map((header, index) => (
              <div key={index} className="flex flex-col sm:flex-row gap-2">
                <Input
                  placeholder="Header name"
                  value={header.key}
                  onChange={(e) => updateHeader(index, 'key', e.target.value)}
                  className="flex-1"
                />
                <div className="flex gap-2">
                  <Input
                    placeholder="Header value"
                    value={header.value}
                    onChange={(e) => updateHeader(index, 'value', e.target.value)}
                    className="flex-1 min-w-0"
                  />
                  <Button type="button" variant="ghost" size="icon" onClick={() => removeHeader(index)} className="flex-shrink-0">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Authentication */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold">Authentication</h3>
        <div>
          <Label htmlFor="authType">Authentication Type</Label>
          <Select value={data.authType} onValueChange={(value) => updateField('authType', value)}>
            <SelectTrigger id="authType" className="mt-1.5">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None</SelectItem>
              <SelectItem value="bearer">Bearer Token</SelectItem>
              <SelectItem value="basic">Basic Auth</SelectItem>
              <SelectItem value="api-key">API Key</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {data.authType === 'bearer' && (
          <div>
            <Label htmlFor="bearerToken">Bearer Token</Label>
            <div className="relative mt-1.5">
              <Input
                id="bearerToken"
                type={showAuthValue ? 'text' : 'password'}
                placeholder="Enter your bearer token"
                value={data.authConfig?.token || ''}
                onChange={(e) => updateField('authConfig', { ...data.authConfig, token: e.target.value })}
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0"
                onClick={() => setShowAuthValue(!showAuthValue)}
              >
                {showAuthValue ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        )}

        {data.authType === 'basic' && (
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                placeholder="Username"
                value={data.authConfig?.username || ''}
                onChange={(e) => updateField('authConfig', { ...data.authConfig, username: e.target.value })}
                className="mt-1.5"
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <div className="relative mt-1.5">
                <Input
                  id="password"
                  type={showAuthValue ? 'text' : 'password'}
                  placeholder="Password"
                  value={data.authConfig?.password || ''}
                  onChange={(e) => updateField('authConfig', { ...data.authConfig, password: e.target.value })}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0"
                  onClick={() => setShowAuthValue(!showAuthValue)}
                >
                  {showAuthValue ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          </div>
        )}

        {data.authType === 'api-key' && (
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="apiKeyName">Key Name</Label>
              <Input
                id="apiKeyName"
                placeholder="e.g., X-API-Key"
                value={data.authConfig?.keyName || ''}
                onChange={(e) => updateField('authConfig', { ...data.authConfig, keyName: e.target.value })}
                className="mt-1.5"
              />
            </div>
            <div>
              <Label htmlFor="apiKeyValue">Key Value</Label>
              <div className="relative mt-1.5">
                <Input
                  id="apiKeyValue"
                  type={showAuthValue ? 'text' : 'password'}
                  placeholder="Enter your API key"
                  value={data.authConfig?.keyValue || ''}
                  onChange={(e) => updateField('authConfig', { ...data.authConfig, keyValue: e.target.value })}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0"
                  onClick={() => setShowAuthValue(!showAuthValue)}
                >
                  {showAuthValue ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
