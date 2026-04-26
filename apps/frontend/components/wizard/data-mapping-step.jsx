'use client'

import { useState, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Database, Search, Filter, ArrowUpDown, Loader2, Play, AlertCircle, CheckCircle2 } from 'lucide-react'
import apiClient from '../../services/apiClient'

export function DataMappingStep({ data, apiConfig, parameters = [], onChange }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [preview, setPreview] = useState(null)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const [sortBy, setSortBy] = useState('sourcePath')

  const selectedFields = data?.selectedFields || []

  const setSelectedFields = (fields) => onChange({ ...data, selectedFields: fields })

  const extractFields = (obj, prefix = '$') => {
    const out = []

    // List of technical fields to skip
    const technicalFields = new Set([
      'status', 'ok', 'success', 'message', 'headers', 'response', 'request',
      'meta', 'pagination', 'page', 'limit', 'total', 'count', 'error',
      'errors', 'warnings', 'info', 'debug', 'trace', 'timestamp', 'version'
    ])

    // List of priority fields to prioritize
    const priorityFields = new Set([
      'id', 'name', 'type', 'location', 'address', 'price', 'cost', 'rating',
      'description', 'coordinates', 'created_at', 'updated_at', 'metadata',
      'title', 'label', 'value', 'code', 'category', 'tags', 'status_code',
      'latitude', 'longitude', 'lat', 'lng', 'lon', 'geo', 'position'
    ])

    const toSnakeCase = (str) => {
      return str
        .replace(/([a-z])([A-Z])/g, '$1_$2') // camelCase -> snake_case
        .replace(/[\s\-]+/g, '_') // spaces/hyphens -> underscores
        .replace(/[^a-zA-Z0-9_]/g, '') // remove special chars
        .toLowerCase()
        .replace(/^_+|_+$/g, '') // trim underscores
    }

    const getFieldType = (val) => {
      if (val === null || val === undefined || val === '') return null
      if (typeof val === 'number') return 'Number'
      if (typeof val === 'boolean') return 'Boolean'
      if (typeof val === 'string') {
        // Check if it's a date string
        if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(val) ||
            /^\d{4}\/\d{2}\/\d{2}/.test(val) ||
            /^\d{2}\/\d{2}\/\d{4}/.test(val)) {
          return 'Date'
        }
        return 'String'
      }
      if (Array.isArray(val)) return 'Array'
      if (typeof val === 'object') return 'Object'
      return 'String'
    }

    const visit = (val, path, isArrayItem = false) => {
      if (val === null || val === undefined || val === '') return

      if (Array.isArray(val)) {
        if (val.length > 0) {
          // Nếu đây là array cấp cao nhất, giả định mỗi phần tử là một document
          const isRootArray = path === '$'
          if (isRootArray) {
            // Thêm array field với [*] notation
            const arrayPath = path + '[*]'
            out.push({
              path: arrayPath,
              suggestedName: 'items',
              type: 'Array',
              sampleValue: val,
              priority: 0
            })
            // Visit first element để lấy sub-fields
            visit(val[0], arrayPath, true)
          } else {
            // Array lồng nhau
            const fieldName = path.split('.').pop()?.split('[')[0] || 'array_field'
            const snakeName = toSnakeCase(fieldName)
            if (!technicalFields.has(snakeName)) {
              out.push({
                path: path + '[*]',
                suggestedName: snakeName,
                type: 'Array',
                sampleValue: val,
                priority: priorityFields.has(snakeName) ? 2 : 1
              })
              // Visit first element
              visit(val[0], path + '[0]', true)
            }
          }
        }
        return
      }

      if (typeof val === 'object') {
        // Visit all object properties
        Object.keys(val).forEach((k) => {
          const snakeKey = toSnakeCase(k)
          // Skip technical fields only at root level, allow them in nested objects
          if (path === '$' && technicalFields.has(snakeKey)) return

          const newPath = path + '.' + k
          visit(val[k], newPath, isArrayItem)
        })
      } else {
        // Đây là leaf field (primitive value)
        const fieldName = path.split('.').pop()?.split('[')[0] || 'field'
        const snakeName = toSnakeCase(fieldName)

        // Skip technical fields
        if (technicalFields.has(snakeName)) return

        // Skip invalid values
        if (val === 'NA' || val === null || val === undefined || val === '') return

        const fieldType = getFieldType(val)
        if (!fieldType) return

        out.push({
          path,
          suggestedName: snakeName,
          type: fieldType,
          sampleValue: val,
          priority: priorityFields.has(snakeName) ? 3 : priorityFields.has(fieldName) ? 2 : 1
        })
      }
    }

    visit(obj, prefix)

    // Sort by priority (high to low), then by path
    out.sort((a, b) => {
      if (a.priority !== b.priority) return b.priority - a.priority
      return a.path.localeCompare(b.path)
    })

    return out
  }

  const testAndDetect = async () => {
    setLoading(true)
    setError('')
    try {
      // Build parameters payload from wizard parameters (support list mode)
      const paramDefs = Array.isArray(parameters)
        ? parameters
            .filter(p => p && p.name && Array.isArray(p.values) && p.values.length > 0)
            .map(p => ({ name: p.name, values: p.values }))
        : []

      const payload = {
        apiConfig: {
          baseUrl: apiConfig?.baseUrl,
          method: apiConfig?.method || 'GET',
          headers: (apiConfig?.headers || []).filter(h => h.key && h.value),
          authType: apiConfig?.authType || 'none',
          authConfig: apiConfig?.authConfig || {},
          // Send parameter definitions so backend can attach them to URL/body
          parameters: paramDefs
        }
      }
      const res = await apiClient.post('/api/test-connection', payload)
      console.log('Full axios response:', res)
      console.log('Response data:', res?.data)

      // Axios already parses JSON responses, so res.data should be the parsed object
      let json = res?.data

      console.log('Parsed json from axios:', json)
      console.log('Response structure check:')
      console.log('- json exists:', !!json)
      console.log('- json is object:', typeof json === 'object')
      console.log('- json.response exists:', json && json.response)
      console.log('- json.response.body exists:', json && json.response && json.response.body)
      console.log('- json.response.body type:', json && json.response && json.response.body ? typeof json.response.body : 'N/A')

      // Extract fields from the actual API response data, not the test metadata
      let dataToExtract = json
      let previewData = json

      // PRIORITY: Always try to extract from response.body if it exists (this is the actual API data)
      if (json && typeof json === 'object' && json.response && json.response.body) {
        console.log('Found response.body, attempting to parse...')
        try {
          // Parse the actual API response from the body
          const rawBody = json.response.body
          console.log('Raw body to parse:', rawBody)
          console.log('Raw body type:', typeof rawBody)

          let parsedBody
          if (typeof rawBody === 'string') {
            parsedBody = JSON.parse(rawBody)
            console.log('Parsed string body:', parsedBody)
          } else {
            parsedBody = rawBody
            console.log('Body was already object:', parsedBody)
          }

          // 3. If body after parsing is still a JSON string → parse one more time
          if (parsedBody && typeof parsedBody === 'string') {
            try {
              const doubleParsed = JSON.parse(parsedBody)
              parsedBody = doubleParsed
              console.log('Double-parsed body (was JSON string):', doubleParsed)
            } catch (doubleParseError) {
              console.log('Body is string but not JSON, keeping as-is')
            }
          }
          // 4. Normalize data structure before extraction
          let normalizedData = parsedBody

          // Automatically find main data array
          if (Array.isArray(parsedBody)) {
            normalizedData = parsedBody
            console.log('Body is already an array, using directly')
          } else if (parsedBody?.body && Array.isArray(parsedBody.body)) {
            normalizedData = parsedBody.body
            console.log('Found array in parsedBody.body')
          } else if (parsedBody?.data && Array.isArray(parsedBody.data)) {
            normalizedData = parsedBody.data
            console.log('Found array in parsedBody.data')
          } else if (parsedBody?.results && Array.isArray(parsedBody.results)) {
            normalizedData = parsedBody.results
            console.log('Found array in parsedBody.results')
          } else if (parsedBody?.items && Array.isArray(parsedBody.items)) {
            normalizedData = parsedBody.items
            console.log('Found array in parsedBody.items')
          } else if (parsedBody?.Prices && Array.isArray(parsedBody.Prices)) {
            normalizedData = parsedBody.Prices
            console.log('Found array in parsedBody.Prices')
          } else if (parsedBody?.products && Array.isArray(parsedBody.products)) {
            normalizedData = parsedBody.products
            console.log('Found array in parsedBody.products')
          } else if (parsedBody?.places && Array.isArray(parsedBody.places)) {
            normalizedData = parsedBody.places
            console.log('Found array in parsedBody.places')
          } else {
            // If array not found, wrap in array to handle as single document
            normalizedData = [parsedBody]
            console.log('No array found, wrapping single object in array')
          }

          dataToExtract = normalizedData
          previewData = normalizedData // Show the normalized data in preview
          console.log('✅ Successfully normalized API data:', normalizedData)
          console.log('Final data type:', Array.isArray(normalizedData) ? 'Array' : typeof normalizedData)
        } catch (parseError) {
          console.warn('❌ Failed to parse response body:', parseError)
          console.log('Raw response body that failed to parse:', json.response.body)
          // Fallback: use response.body as-is
          dataToExtract = json.response.body
          previewData = json.response.body
        }
      } else {
        // No response.body found, try to normalize the raw response
        console.log('❌ No response.body found, normalizing raw response data')
        console.log('Raw json:', json)

        let normalizedData = json

        // Try to find array in common locations
        if (Array.isArray(json)) {
          normalizedData = json
        } else if (json?.data && Array.isArray(json.data)) {
          normalizedData = json.data
        } else if (json?.results && Array.isArray(json.results)) {
          normalizedData = json.results
        } else if (json?.items && Array.isArray(json.items)) {
          normalizedData = json.items
        } else {
          normalizedData = [json]
        }

        dataToExtract = normalizedData
        previewData = normalizedData
      }
      
      setPreview(previewData)
      
      if (dataToExtract && typeof dataToExtract === 'object') {
        const fields = extractFields(dataToExtract)
        console.log('Final extracted fields for mapping:', fields)
        console.log('Field mapping summary:')
        fields.forEach(f => {
          console.log(`  ${f.path} -> ${f.suggestedName} (${f.type})`)
        })

        if ((data?.selectedFields || []).length === 0) {
          setSelectedFields(
            fields.map((f) => ({
              sourcePath: f.path,
              targetField: f.suggestedName,
              dataType: f.type,
              isSelected: true,
            }))
          )
        }
      }
    } catch (e) {
      setError(e?.message || 'Failed to test connection')
    } finally {
      setLoading(false)
    }
  }

  const filtered = useMemo(() => {
    let arr = [...selectedFields]
    if (search) {
      const q = search.toLowerCase()
      arr = arr.filter((f) => f.sourcePath.toLowerCase().includes(q) || f.targetField.toLowerCase().includes(q))
    }
    if (typeFilter !== 'all') arr = arr.filter((f) => f.dataType === typeFilter)
    arr.sort((a, b) => {
      if (sortBy === 'sourcePath') return a.sourcePath.localeCompare(b.sourcePath)
      if (sortBy === 'targetField') return a.targetField.localeCompare(b.targetField)
      if (sortBy === 'dataType') return a.dataType.localeCompare(b.dataType)
      return 0
    })
    return arr
  }, [selectedFields, search, typeFilter, sortBy])

  const updateRow = (idx, patch) => {
    const next = [...selectedFields]
    next[idx] = { ...next[idx], ...patch }
    setSelectedFields(next)
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Test API Connection</CardTitle>
          <CardDescription>Gọi thử endpoint để dò cấu trúc dữ liệu</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2">
            <Button onClick={testAndDetect} disabled={!apiConfig?.baseUrl || loading} className="gap-2">
              {loading ? (<><Loader2 className="h-4 w-4 animate-spin" />Đang kiểm tra...</>) : (<><Play className="h-4 w-4" />Test Connection</>)}
            </Button>
            {preview && !error && (
              <span className="flex items-center gap-1 text-green-600 text-sm"><CheckCircle2 className="h-4 w-4" />OK</span>
            )}
            {error && (
              <span className="flex items-center gap-1 text-destructive text-sm"><AlertCircle className="h-4 w-4" />{error}</span>
            )}
          </div>
          {preview && (
            <div className="space-y-2">
              <div className="text-xs text-muted-foreground">API Response Data (normalized for mapping):</div>
              <ScrollArea className="h-40 w-full rounded border bg-muted/40">
                <pre className="p-3 text-xs whitespace-pre-wrap break-all">{JSON.stringify(preview, null, 2)}</pre>
              </ScrollArea>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Field Mapping</CardTitle>
          <CardDescription>Automatically normalize API data and map to api_places collection (handle JSON strings, find main data array)</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="tableName">Target Table Name</Label>
            <Input id="tableName" value={data?.tableName || ''} onChange={(e) => onChange({ ...data, tableName: e.target.value })} placeholder="api_places" />
          </div>

          <div className="grid gap-2 sm:grid-cols-3">
            <div className="sm:col-span-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input className="pl-9" placeholder="Search by source/target" value={search} onChange={(e) => setSearch(e.target.value)} />
              </div>
            </div>
            <div className="sm:col-span-1">
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger><Filter className="h-4 w-4 mr-2" /><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="string">String</SelectItem>
                  <SelectItem value="number">Number</SelectItem>
                  <SelectItem value="boolean">Boolean</SelectItem>
                  <SelectItem value="date">Date</SelectItem>
                  <SelectItem value="array">Array</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="sm:col-span-1">
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger><ArrowUpDown className="h-4 w-4 mr-2" /><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="sourcePath">Source Path</SelectItem>
                  <SelectItem value="targetField">Target Field</SelectItem>
                  <SelectItem value="dataType">Data Type</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="rounded border overflow-hidden">
            <div className="hidden md:grid md:grid-cols-12 gap-2 px-3 py-2 bg-muted/50 text-xs text-muted-foreground">
              <div className="col-span-1">Use</div>
              <div className="col-span-5">Source Path</div>
              <div className="col-span-4">Target Field</div>
              <div className="col-span-2">Type</div>
            </div>
            <ScrollArea className={`${filtered.length > 10 ? 'h-80' : 'h-auto'}`}>
              {filtered.length === 0 ? (
                <div className="p-6 text-center text-sm text-muted-foreground">
                  <Database className="h-6 w-6 mx-auto mb-2 opacity-60" />No fields available
                </div>
              ) : filtered.map((f, i) => {
                const idx = selectedFields.findIndex((x) => x === f)
                return (
                  <div key={`row-${idx}`} className="grid md:grid-cols-12 gap-2 p-2 border-t first:border-t-0 items-center">
                    <div className="md:col-span-1">
                      <Checkbox checked={!!f.isSelected} onCheckedChange={(v) => updateRow(idx, { isSelected: !!v })} />
                    </div>
                    <div className="md:col-span-5">
                      <code className="text-xs bg-muted px-2 py-1 rounded block truncate" title={f.sourcePath}>{f.sourcePath}</code>
                    </div>
                    <div className="md:col-span-4">
                      <Input value={f.targetField} onChange={(e) => updateRow(idx, { targetField: e.target.value })} placeholder="column_name" />
                    </div>
                    <div className="md:col-span-2">
                      <Select value={f.dataType} onValueChange={(v) => updateRow(idx, { dataType: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="string">String</SelectItem>
                          <SelectItem value="number">Number</SelectItem>
                          <SelectItem value="boolean">Boolean</SelectItem>
                          <SelectItem value="date">Date</SelectItem>
                          <SelectItem value="array">Array</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                )
              })}
            </ScrollArea>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
