'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Plus, Trash2, Upload, Info } from 'lucide-react'
import { Switch } from '@/components/ui/switch'

export function ParametersStep({ data, onChange }) {
  const [editingParam, setEditingParam] = useState(null)

  const addParameter = () => {
    const newParam = {
      id: Math.random().toString(36).substr(2, 9),
      name: '',
      type: 'query',
      mode: 'list',
      values: [],
      isRequired: false,
    }
    setEditingParam(newParam)
  }

  const saveParameter = () => {
    if (!editingParam) return
    const existingIndex = data.findIndex((p) => p.id === editingParam.id)
    if (existingIndex >= 0) {
      const newData = [...data]
      newData[existingIndex] = editingParam
      onChange(newData)
    } else {
      onChange([...data, editingParam])
    }
    setEditingParam(null)
  }

  const deleteParameter = (id) => {
    onChange(data.filter((p) => p.id !== id))
  }

  const editParameter = (param) => {
    setEditingParam({ ...param })
  }

  return (
    <div className="space-y-6">
      {/* Info Banner */}
      <Card className="bg-muted/50 border-muted">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <Info className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium">Parameter Modes</p>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>
                  <strong>List:</strong> Execute API once for each value
                </li>
                <li>
                  <strong>Cartesian:</strong> Generate all combinations of multiple parameters
                </li>
                <li>
                  <strong>Template:</strong> Use dynamic templates with variables
                </li>
                <li>
                  <strong>Dynamic:</strong> Generate values based on date ranges or previous runs
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Parameters List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">Configured Parameters</h3>
          <Button onClick={addParameter} className="gap-2">
            <Plus className="h-4 w-4" />
            Add Parameter
          </Button>
        </div>

        {data.length === 0 && !editingParam ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-8">
              <p className="text-sm text-muted-foreground mb-4">No parameters configured yet</p>
              <Button onClick={addParameter} variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Add Your First Parameter
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2">
            {data.map((param) => (
              <Card key={param.id}>
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <p className="font-medium">{param.name}</p>
                        <Badge variant="outline">{param.type}</Badge>
                        <Badge variant="secondary">{param.mode}</Badge>
                        {param.isRequired && <Badge>Required</Badge>}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {param.mode === 'list' && `${param.values.length} values`}
                        {param.mode === 'cartesian' && `${param.values.length} values (cartesian product)`}
                        {param.mode === 'template' && `Template: ${param.template}`}
                        {param.mode === 'dynamic' && 'Dynamic generation'}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => editParameter(param)}>
                        Edit
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => deleteParameter(param.id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Parameter Editor */}
      {editingParam && (
        <Card className="border-primary">
          <CardHeader>
            <CardTitle>{editingParam.name || 'New Parameter'}</CardTitle>
            <CardDescription>Configure parameter details and values</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Basic Info */}
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="paramName">Parameter Name *</Label>
                <Input
                  id="paramName"
                  placeholder="e.g., user_id"
                  value={editingParam.name}
                  onChange={(e) => setEditingParam({ ...editingParam, name: e.target.value })}
                  className="mt-1.5"
                />
              </div>
              <div>
                <Label htmlFor="paramType">Parameter Type</Label>
                <Select
                  value={editingParam.type}
                  onValueChange={(value) => setEditingParam({ ...editingParam, type: value })}
                >
                  <SelectTrigger id="paramType" className="mt-1.5">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="query">Query Parameter</SelectItem>
                    <SelectItem value="path">Path Parameter</SelectItem>
                    <SelectItem value="body">Body Parameter</SelectItem>
                    <SelectItem value="header">Header Parameter</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="required">Required Parameter</Label>
              <Switch
                id="required"
                checked={editingParam.isRequired}
                onCheckedChange={(checked) => setEditingParam({ ...editingParam, isRequired: checked })}
              />
            </div>

            {/* Mode Selection */}
            <div>
              <Label>Parameter Mode</Label>
              <Tabs
                value={editingParam.mode}
                onValueChange={(value) => setEditingParam({ ...editingParam, mode: value })}
                className="mt-1.5"
              >
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="list">List</TabsTrigger>
                  <TabsTrigger value="cartesian">Cartesian</TabsTrigger>
                  <TabsTrigger value="template">Template</TabsTrigger>
                  <TabsTrigger value="dynamic">Dynamic</TabsTrigger>
                </TabsList>

                <TabsContent value="list" className="space-y-4 mt-4">
                  <div>
                    <Label htmlFor="listValues">Values (one per line)</Label>
                    <Textarea
                      id="listValues"
                      placeholder={'value1\nvalue2\nvalue3'}
                      value={editingParam.values.join('\n')}
                      onChange={(e) =>
                        setEditingParam({
                          ...editingParam,
                          values: e.target.value.split('\n').filter((v) => v.trim()),
                        })
                      }
                      className="mt-1.5 font-mono"
                      rows={6}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      API will be called once for each value ({editingParam.values.length} requests)
                    </p>
                  </div>
                  <Button variant="outline" className="gap-2 bg-transparent">
                    <Upload className="h-4 w-4" />
                    Import from CSV
                  </Button>
                </TabsContent>

                <TabsContent value="cartesian" className="space-y-4 mt-4">
                  <div>
                    <Label htmlFor="cartesianValues">Values (one per line)</Label>
                    <Textarea
                      id="cartesianValues"
                      placeholder={'value1\nvalue2\nvalue3'}
                      value={editingParam.values.join('\n')}
                      onChange={(e) =>
                        setEditingParam({
                          ...editingParam,
                          values: e.target.value.split('\n').filter((v) => v.trim()),
                        })
                      }
                      className="mt-1.5 font-mono"
                      rows={6}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Will combine with other cartesian parameters to generate all possible combinations
                    </p>
                  </div>
                </TabsContent>

                <TabsContent value="template" className="space-y-4 mt-4">
                  <div>
                    <Label htmlFor="template">Template String</Label>
                    <Input
                      id="template"
                      placeholder={'e.g., user_{{id}}_{{date}}'}
                      value={editingParam.template || ''}
                      onChange={(e) => setEditingParam({ ...editingParam, template: e.target.value })}
                      className="mt-1.5 font-mono"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Use {'{{variable}}'} syntax for dynamic values</p>
                  </div>
                </TabsContent>

                <TabsContent value="dynamic" className="space-y-4 mt-4">
                  <div>
                    <Label htmlFor="dynamicType">Dynamic Type</Label>
                    <Select defaultValue="date_range">
                      <SelectTrigger id="dynamicType" className="mt-1.5">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="date_range">Date Range</SelectItem>
                        <SelectItem value="incremental_id">Incremental ID</SelectItem>
                        <SelectItem value="last_run">Based on Last Run</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Label htmlFor="startDate">Start Date</Label>
                      <Input id="startDate" type="date" className="mt-1.5" />
                    </div>
                    <div>
                      <Label htmlFor="endDate">End Date</Label>
                      <Input id="endDate" type="date" className="mt-1.5" />
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setEditingParam(null)}>
                Cancel
              </Button>
              <Button onClick={saveParameter} disabled={!editingParam.name}>
                Save Parameter
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
