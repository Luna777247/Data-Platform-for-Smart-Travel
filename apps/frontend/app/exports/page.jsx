"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Download, Trash2, AlertCircle, Plus } from "lucide-react"
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
import { ExportFormDialog } from "@/components/exports/export-form-dialog.jsx"

export default function ExportsPage() {
  const [exports, setExports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    loadExports()
  }, [])

  async function loadExports() {
    try {
      setLoading(true)
      const res = await apiClient.get("/api/exports")
      setExports(res.data || [])
    } catch (err) {
      console.error("[v0] Error fetching exports:", err)
      setError("Failed to load exports")
    } finally {
      setLoading(false)
    }
  }

  const deleteExport = async (exportId) => {
    setDeletingId(exportId)
    try {
      await apiClient.delete(`/api/exports/${exportId}`)
      setExports(exports.filter((e) => e.id !== exportId))
    } catch (err) {
      console.error("[v0] Error deleting export:", err)
      setError("Failed to delete export")
    } finally {
      setDeletingId(null)
    }
  }

  const downloadExport = async (exportId) => {
    try {
      const res = await apiClient.get(`/api/exports/${exportId}/download`, { responseType: "blob" })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement("a")
      link.href = url
      link.setAttribute("download", `export-${exportId}.zip`)
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
    } catch (err) {
      console.error("[v0] Error downloading export:", err)
      setError("Failed to download export")
    }
  }

  const filteredExports = exports.filter(
    (e) =>
      e.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.description?.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <PageLayout
      title="Data Exports"
      description="Manage and download data exports"
      showBackButton={true}
      headerActions={
        <ExportFormDialog
          onSave={loadExports}
          trigger={
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              New Export
            </Button>
          }
        />
      }
    >
      {error && (
        <Card className="border-destructive mb-6">
          <CardContent className="flex items-center gap-3 py-4">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <p className="text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      <div className="mb-6">
        <Input
          placeholder="Search exports..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Exports</CardTitle>
          <CardDescription>View and manage your data exports</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading exports...</div>
          ) : filteredExports.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">No exports found</div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Format</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredExports.map((exp) => (
                    <TableRow key={exp.id}>
                      <TableCell className="font-medium">{exp.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{exp.format}</Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {(exp.size / 1024 / 1024).toFixed(2)} MB
                      </TableCell>
                      <TableCell>
                        <Badge variant={exp.status === "completed" ? "default" : "secondary"}>{exp.status}</Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(exp.createdAt).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => downloadExport(exp.id)}
                            disabled={exp.status !== "completed"}
                            className="gap-1"
                          >
                            <Download className="h-4 w-4" />
                            <span className="hidden sm:inline">Download</span>
                          </Button>
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button variant="ghost" size="sm" className="text-destructive">
                                {deletingId === exp.id ? "..." : <Trash2 className="h-4 w-4" />}
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Delete export?</AlertDialogTitle>
                                <AlertDialogDescription>
                                  This action cannot be undone. The export "{exp.name}" will be permanently deleted.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction onClick={() => deleteExport(exp.id)}>Delete</AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </PageLayout>
  )
}
