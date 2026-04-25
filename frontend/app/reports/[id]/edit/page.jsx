"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { PageLayout } from "@/components/ui/page-layout"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"
import apiClient from "../../../../services/apiClient.js"

export default function EditReportPage() {
  const params = useParams()
  const router = useRouter()
  const reportId = params.id
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [formData, setFormData] = useState(null)

  useEffect(() => {
    loadReport()
  }, [reportId])

  async function loadReport() {
    try {
      setLoading(true)
      const res = await apiClient.get(`/api/reports/${reportId}`)
      setFormData(res.data)
    } catch (err) {
      console.error("[v0] Error fetching report:", err)
      setError("Failed to load report")
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await apiClient.put(`/api/reports/${reportId}`, formData)
      router.push(`/reports/${reportId}`)
    } catch (err) {
      console.error("[v0] Error updating report:", err)
      setError(err.response?.data?.message || "Failed to update report")
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <PageLayout title="Loading..." showBackButton={true}></PageLayout>
  }

  if (!formData) {
    return (
      <PageLayout title="Report Not Found" showBackButton={true}>
        <Card className="border-destructive">
          <CardContent className="py-8 text-center">
            <p className="text-destructive mb-4">{error || "Report not found"}</p>
            <Link href="/reports">
              <Button>Back to Reports</Button>
            </Link>
          </CardContent>
        </Card>
      </PageLayout>
    )
  }

  return (
    <PageLayout title={`Edit: ${formData.name}`} showBackButton={true}>
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
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="name">Report Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Report Configuration</CardTitle>
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
            <Link href={`/reports/${reportId}`}>
              <Button variant="outline" className="gap-2 bg-transparent">
                <ArrowLeft className="h-4 w-4" />
                Cancel
              </Button>
            </Link>
            <Button type="submit" disabled={saving}>
              {saving ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </form>
      </div>
    </PageLayout>
  )
}
