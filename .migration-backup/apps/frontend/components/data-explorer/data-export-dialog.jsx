"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Download, Clock } from "lucide-react"
import apiClient from "../../services/apiClient.js"

export function DataExportDialog({ connection }) {
  const [open, setOpen] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [exportFormat, setExportFormat] = useState("csv")
  const [includeMetadata, setIncludeMetadata] = useState(true)

  const handleExport = async () => {
    setExporting(true)
    try {
      // Step 1: Initiate export and get exportId
      const exportRes = await apiClient.post(`/api/data/export`, {
        connectionId: connection.connectionId,
        format: exportFormat,
        includeMetadata,
      })

      const { exportId, filename } = exportRes.data

      // Step 2: Download the actual file
      const downloadRes = await apiClient.get(`/api/data/export/${exportId}`, {
        responseType: 'blob' // Important: get binary data
      })

      // Create download link
      const url = window.URL.createObjectURL(new Blob([downloadRes.data]))
      const link = document.createElement("a")
      link.href = url
      link.setAttribute("download", filename || `${connection.connectionId}-export.${exportFormat}`)
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
      window.URL.revokeObjectURL(url)

      setOpen(false)
    } catch (err) {
      console.error("[v0] Error exporting data:", err)
    } finally {
      setExporting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2 bg-transparent">
          <Download className="h-4 w-4" />
          Export
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Export Data</DialogTitle>
          <DialogDescription>Export data from {connection.connectionId}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <Label htmlFor="format">Export Format</Label>
            <Select value={exportFormat} onValueChange={setExportFormat}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="csv">CSV</SelectItem>
                <SelectItem value="json">JSON</SelectItem>
                {/* <SelectItem value="xlsx">Excel (XLSX)</SelectItem> */}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox id="metadata" checked={includeMetadata} onCheckedChange={setIncludeMetadata} />
            <Label htmlFor="metadata">Include Metadata</Label>
          </div>

          <div className="text-sm text-muted-foreground">
            <p>Records: {connection.totalRecords}</p>
            <p>Size: ~{(connection.totalRecords * 0.001).toFixed(2)} MB</p>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleExport} disabled={exporting} className="gap-2">
              {exporting ? (
                <>
                  <Clock className="h-4 w-4 animate-spin" />
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4" />
                  Export
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
