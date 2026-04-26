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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import apiClient from "../../services/apiClient.js"

export function ExportFormDialog({ onSave, trigger }) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    format: "csv",
    includeMetadata: true,
    compression: true,
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await apiClient.post("/api/exports", formData)
      setOpen(false)
      setFormData({
        name: "",
        description: "",
        format: "csv",
        includeMetadata: true,
        compression: true,
      })
      onSave?.()
    } catch (err) {
      console.error("[v0] Error creating export:", err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Export</DialogTitle>
          <DialogDescription>Configure and create a new data export</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="name">Export Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Monthly Data Export"
              required
            />
          </div>
          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe what data is included"
              rows={2}
            />
          </div>
          <div>
            <Label htmlFor="format">Export Format</Label>
            <Select value={formData.format} onValueChange={(value) => setFormData({ ...formData, format: value })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="csv">CSV</SelectItem>
                <SelectItem value="json">JSON</SelectItem>
                <SelectItem value="xlsx">Excel (XLSX)</SelectItem>
                <SelectItem value="parquet">Parquet</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="includeMetadata"
                checked={formData.includeMetadata}
                onCheckedChange={(checked) => setFormData({ ...formData, includeMetadata: checked })}
              />
              <Label htmlFor="includeMetadata">Include Metadata</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="compression"
                checked={formData.compression}
                onCheckedChange={(checked) => setFormData({ ...formData, compression: checked })}
              />
              <Label htmlFor="compression">Enable Compression</Label>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Creating..." : "Create Export"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
