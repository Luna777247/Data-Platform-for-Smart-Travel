"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { PageLayout } from "@/components/ui/page-layout"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"
import apiClient from "../../../services/apiClient.js"

export default function NewReportPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    type: "summary",
    dataSource: "",
    schedule: "manual",
    includeCharts: true,
    includeTables: true,
    includeMetrics: true,
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await apiClient.post("/api/reports", formData)
      router.push(`/reports/${res.data.id}`)
    } catch (err) {
      console.error("[v0] Error creating report:", err)
      setError(err.response?.data?.message || "Failed to create report")
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageLayout title="Create New Report" showBackButton={true}>
      <div className="max-w-2xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <Card className="border-destructive">
              <CardContent className="py-4 text-sm text-destructive">{error}</CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Report Details</CardTitle>
              <CardDescription>Basic information about your report</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="name">Report Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Monthly Sales Report"
                  required
                />
              </div>
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe what this report contains"
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Report Configuration</CardTitle>
              <CardDescription>Configure report type and data source</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="type">Report Type</Label>
                <Select value={formData.type} onValueChange={(value) => setFormData({ ...formData, type: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="summary">Summary Report</SelectItem>
                    <SelectItem value="detailed">Detailed Report</SelectItem>
                    <SelectItem value="analytics">Analytics Report</SelectItem>
                    <SelectItem value="custom">Custom Report</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="dataSource">Data Source</Label>
                <Select
                  value={formData.dataSource}
                  onValueChange={(value) => setFormData({ ...formData, dataSource: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a data source" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="connections">API Connections</SelectItem>
                    <SelectItem value="runs">Pipeline Runs</SelectItem>
                    <SelectItem value="schedules">Schedules</SelectItem>
                    <SelectItem value="analytics">Analytics Data</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="schedule">Report Schedule</Label>
                <Select
                  value={formData.schedule}
                  onValueChange={(value) => setFormData({ ...formData, schedule: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="manual">Manual</SelectItem>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                    <SelectItem value="monthly">Monthly</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Report Components</CardTitle>
              <CardDescription>Choose what to include in your report</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="includeCharts"
                  checked={formData.includeCharts}
                  onCheckedChange={(checked) => setFormData({ ...formData, includeCharts: checked })}
                />
                <Label htmlFor="includeCharts">Include Charts</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="includeTables"
                  checked={formData.includeTables}
                  onCheckedChange={(checked) => setFormData({ ...formData, includeTables: checked })}
                />
                <Label htmlFor="includeTables">Include Tables</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="includeMetrics"
                  checked={formData.includeMetrics}
                  onCheckedChange={(checked) => setFormData({ ...formData, includeMetrics: checked })}
                />
                <Label htmlFor="includeMetrics">Include Metrics</Label>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-between gap-2">
            <Link href="/reports">
              <Button variant="outline" className="gap-2 bg-transparent">
                <ArrowLeft className="h-4 w-4" />
                Cancel
              </Button>
            </Link>
            <Button type="submit" disabled={loading}>
              {loading ? "Creating..." : "Create Report"}
            </Button>
          </div>
        </form>
      </div>
    </PageLayout>
  )
}
