"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { AlertCircle, CheckCircle } from "lucide-react"
import apiClient from "../../services/apiClient.js"

export function AdminSystemSettings() {
  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  async function loadSettings() {
    try {
      setLoading(true)
      const res = await apiClient.get("/api/system/settings")
      setSettings(res.data || {})
    } catch (err) {
      console.error("[v0] Error fetching settings:", err)
      setError("Failed to load system settings")
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    setSuccess(false)
    try {
      await apiClient.put("/api/system/settings", settings)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      console.error("[v0] Error saving settings:", err)
      setError("Failed to save settings")
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="text-center py-8 text-muted-foreground">Loading settings...</div>
  }

  return (
    <div className="space-y-6">
      {error && (
        <Card className="border-destructive">
          <CardContent className="flex items-center gap-3 py-4">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <p className="text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {success && (
        <Card className="border-green-500">
          <CardContent className="flex items-center gap-3 py-4">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <p className="text-sm text-green-500">Settings saved successfully</p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>General Settings</CardTitle>
          <CardDescription>Configure system-wide settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label htmlFor="appName">Application Name</Label>
            <Input
              id="appName"
              value={settings?.appName || ""}
              onChange={(e) => setSettings({ ...settings, appName: e.target.value })}
            />
          </div>

          <div>
            <Label htmlFor="appDescription">Application Description</Label>
            <Textarea
              id="appDescription"
              value={settings?.appDescription || ""}
              onChange={(e) => setSettings({ ...settings, appDescription: e.target.value })}
              rows={3}
            />
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Enable User Registration</Label>
                <p className="text-sm text-muted-foreground">Allow new users to register</p>
              </div>
              <Switch
                checked={settings?.enableRegistration || false}
                onCheckedChange={(checked) => setSettings({ ...settings, enableRegistration: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>Enable API Access</Label>
                <p className="text-sm text-muted-foreground">Allow API access for integrations</p>
              </div>
              <Switch
                checked={settings?.enableAPI || false}
                onCheckedChange={(checked) => setSettings({ ...settings, enableAPI: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>Enable Audit Logging</Label>
                <p className="text-sm text-muted-foreground">Log all system activities</p>
              </div>
              <Switch
                checked={settings?.enableAuditLog || false}
                onCheckedChange={(checked) => setSettings({ ...settings, enableAuditLog: checked })}
              />
            </div>
          </div>

          <div>
            <Label htmlFor="maxConnections">Max Concurrent Connections</Label>
            <Input
              id="maxConnections"
              type="number"
              value={settings?.maxConnections || 100}
              onChange={(e) => setSettings({ ...settings, maxConnections: Number.parseInt(e.target.value) })}
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={loadSettings}>
              Reset
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? "Saving..." : "Save Settings"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
