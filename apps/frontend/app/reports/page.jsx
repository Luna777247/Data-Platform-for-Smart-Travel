"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Plus, FileText, Trash2, Edit2, Eye, Clock } from "lucide-react"
import { PageLayout } from "@/components/ui/page-layout"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import apiClient from "../../services/apiClient.js"

export default function ReportsPage() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    loadReports()
  }, [])

  async function loadReports() {
    try {
      setLoading(true)
      const res = await apiClient.get("/api/reports")
      setReports(res.data || [])
    } catch (err) {
      console.error("[v0] Error fetching reports:", err)
      setError("Failed to load reports")
    } finally {
      setLoading(false)
    }
  }

  const deleteReport = async (reportId) => {
    setDeletingId(reportId)
    try {
      await apiClient.delete(`/api/reports/${reportId}`)
      setReports(reports.filter((r) => r.id !== reportId))
    } catch (err) {
      console.error("[v0] Error deleting report:", err)
      setError("Failed to delete report")
    } finally {
      setDeletingId(null)
    }
  }

  const filteredReports = reports.filter(
    (r) =>
      r.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.description?.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <PageLayout
      title="Reports"
      description="Create and manage data reports"
      showBackButton={true}
      headerActions={
        <Link href="/reports/new">
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            New Report
          </Button>
        </Link>
      }
    >
      {error && (
        <Card className="border-destructive mb-6">
          <CardContent className="flex items-center gap-3 py-4">
            <p className="text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      <div className="mb-6">
        <Input
          placeholder="Search reports..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">Loading reports...</div>
      ) : filteredReports.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No reports found</h3>
            <p className="text-muted-foreground text-center mb-4">Create your first report to get started</p>
            <Link href="/reports/new">
              <Button>Create Report</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredReports.map((report) => (
            <Card key={report.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <CardTitle className="text-lg">{report.name}</CardTitle>
                      <Badge variant={report.status === "active" ? "default" : "secondary"}>{report.status}</Badge>
                    </div>
                    <CardDescription>{report.description || "No description"}</CardDescription>
                    <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
                      <span>Type: {report.type}</span>
                      <span>Created: {new Date(report.createdAt).toLocaleDateString()}</span>
                      <span>Last run: {report.lastRun ? new Date(report.lastRun).toLocaleDateString() : "Never"}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link href={`/reports/${report.id}`}>
                      <Button variant="outline" size="sm" className="gap-2 bg-transparent">
                        <Eye className="h-4 w-4" />
                        View
                      </Button>
                    </Link>
                    <Link href={`/reports/${report.id}/edit`}>
                      <Button variant="outline" size="sm">
                        <Edit2 className="h-4 w-4" />
                      </Button>
                    </Link>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="destructive" size="sm">
                          {deletingId === report.id ? (
                            <Clock className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Delete report?</AlertDialogTitle>
                          <AlertDialogDescription>
                            This action cannot be undone. The report "{report.name}" will be permanently deleted.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction onClick={() => deleteReport(report.id)}>Delete</AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>
      )}
    </PageLayout>
  )
}
