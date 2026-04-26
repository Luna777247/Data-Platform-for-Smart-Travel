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
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import apiClient from "../../services/apiClient.js"

const AVAILABLE_PERMISSIONS = [
  "users.read",
  "users.create",
  "users.update",
  "users.delete",
  "roles.read",
  "roles.create",
  "roles.update",
  "roles.delete",
  "connections.read",
  "connections.create",
  "connections.update",
  "connections.delete",
  "schedules.read",
  "schedules.create",
  "schedules.update",
  "schedules.delete",
  "runs.read",
  "runs.execute",
  "system.read",
  "system.update",
  "backups.read",
  "backups.create",
  "backups.restore",
]

export function RoleFormDialog({ role, onSave, trigger }) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState(
    role || {
      name: "",
      description: "",
      permissions: [],
    },
  )

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (role?.id) {
        await apiClient.put(`/api/roles/${role.id}`, formData)
      } else {
        await apiClient.post("/api/roles", formData)
      }
      setOpen(false)
      onSave?.()
    } catch (err) {
      console.error("[v0] Error saving role:", err)
    } finally {
      setLoading(false)
    }
  }

  const togglePermission = (permission) => {
    setFormData({
      ...formData,
      permissions: formData.permissions.includes(permission)
        ? formData.permissions.filter((p) => p !== permission)
        : [...formData.permissions, permission],
    })
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{role ? "Edit Role" : "Add New Role"}</DialogTitle>
          <DialogDescription>{role ? "Update role information" : "Create a new system role"}</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="name">Role Name</Label>
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
          <div>
            <Label>Permissions</Label>
            <div className="grid grid-cols-2 gap-3 mt-2 p-3 border rounded-md bg-muted/50">
              {AVAILABLE_PERMISSIONS.map((perm) => (
                <div key={perm} className="flex items-center space-x-2">
                  <Checkbox
                    id={perm}
                    checked={formData.permissions.includes(perm)}
                    onCheckedChange={() => togglePermission(perm)}
                  />
                  <Label htmlFor={perm} className="text-xs font-normal cursor-pointer">
                    {perm}
                  </Label>
                </div>
              ))}
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Saving..." : "Save"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
