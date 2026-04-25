"use client"

import { useState, useEffect } from "react"
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
import apiClient from "../../services/apiClient.js"

export function ScheduleFormDialog({ schedule, onSave, trigger, open: externalOpen, onOpenChange }) {
  const [internalOpen, setInternalOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [connections, setConnections] = useState([])
  const [formData, setFormData] = useState(
    schedule || {
      connectionId: "",
      connectionName: "",
      description: "",
      scheduleType: "cron",
      cronExpression: "0 0 * * *",
      isActive: true,
    },
  )
  
  // Use external open state if provided, otherwise use internal state
  const isOpen = externalOpen !== undefined ? externalOpen : internalOpen
  const setIsOpen = (newOpen) => {
    if (onOpenChange) {
      onOpenChange(newOpen)
    } else {
      setInternalOpen(newOpen)
    }
  }

  // Update form data when the schedule prop changes
  useEffect(() => {
    if (schedule) {
      setFormData({
        id: schedule.id || schedule._id || "",
        connectionId: schedule.connectionId || "",
        connectionName: schedule.connectionName || "",
        description: schedule.description || "",
        scheduleType: schedule.scheduleType || "cron",
        cronExpression: schedule.cronExpression || "0 0 * * *",
        isActive: schedule.isActive ?? true,
      })
    } else {
      setFormData({
        id: "",
        connectionId: "",
        connectionName: "",
        description: "",
        scheduleType: "cron",
        cronExpression: "0 0 * * *",
        isActive: true,
      })
    }
  }, [schedule]) // Only depend on schedule prop

  // Fetch connections when dialog opens
  useEffect(() => {
    if (isOpen) {
      fetchConnections()
    }
  }, [isOpen])

  const fetchConnections = async () => {
    try {
      const response = await apiClient.get("/api/connections")
      setConnections(response.data || [])
    } catch (err) {
      console.error("[v0] Error fetching connections:", err)
    }
  }

  const handleConnectionChange = (connectionId) => {
    const connection = connections.find(c => c.id === connectionId || c._id === connectionId)
    setFormData({
      ...formData,
      connectionId: connectionId,
      connectionName: connection ? connection.name || connection.connectionName || `${connection.method} ${connection.endpoint}` : "",
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    
    // Only include fields that can be changed
    const dataToSend = {
      description: formData.description,
      scheduleType: formData.scheduleType,
      cronExpression: formData.cronExpression,
      isActive: formData.isActive
    }
    
    try {
      const endpoint = formData.id 
        ? `/api/schedules/${formData.id}`
        : '/api/schedules'
      
      const method = formData.id ? 'put' : 'post'
      
      // For new schedules, include the connection info
      if (!formData.id) {
        dataToSend.connectionId = formData.connectionId
        dataToSend.connectionName = formData.connectionName
      }
      
      // Make the API call with the appropriate method
      const response = await apiClient[method](endpoint, dataToSend)
      
      // Close the dialog and pass the updated data to parent
      setIsOpen(false)
      if (onSave) {
        onSave(response.data || response) // Handle both response formats
      }
    } catch (err) {
      console.error("[v0] Error saving schedule:", err)
      // You might want to show an error message to the user here
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      {trigger && <DialogTrigger asChild>{trigger}</DialogTrigger>}
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{schedule ? "Edit Schedule" : "Create Schedule"}</DialogTitle>
          <DialogDescription>
            {schedule ? "Update schedule configuration" : "Create a new automated schedule"}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="connectionId">Connection</Label>
            {schedule ? (
              // Show read-only input when editing
              <Input
                value={formData.connectionName || 'N/A'}
                disabled={true}
                className="mt-1 bg-muted/50"
              />
            ) : (
              // Show select for new schedule
              <Select
                value={formData.connectionId}
                onValueChange={handleConnectionChange}
                disabled={loading}
                required
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Select a connection" />
                </SelectTrigger>
                <SelectContent>
                  {connections.map((conn) => (
                    <SelectItem key={conn.id || conn._id} value={conn.id || conn._id}>
                      {conn.name || conn.connectionName || `${conn.method} ${conn.endpoint}`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {schedule && (
              <p className="text-xs text-muted-foreground mt-1">
                Connection cannot be changed for existing schedules
              </p>
            )}
          </div>
          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={2}
            />
          </div>
          <div>
            <Label htmlFor="scheduleType">Schedule Type</Label>
            <Select
              value={formData.scheduleType}
              onValueChange={(value) => setFormData({ ...formData, scheduleType: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="cron">Cron Expression</SelectItem>
                <SelectItem value="interval">Interval</SelectItem>
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="weekly">Weekly</SelectItem>
                <SelectItem value="monthly">Monthly</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="cronExpression">Cron Expression</Label>
            <Input
              id="cronExpression"
              value={formData.cronExpression}
              onChange={(e) => setFormData({ ...formData, cronExpression: e.target.value })}
              placeholder="0 0 * * *"
            />
            <p className="text-xs text-muted-foreground mt-1">Format: minute hour day month weekday</p>
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setIsOpen(false)}>
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
