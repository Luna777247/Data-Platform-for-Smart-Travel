"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Users, Shield, Settings, HardDrive, AlertCircle } from "lucide-react"
import { PageLayout } from "@/components/ui/page-layout"
import apiClient from "../../services/apiClient.js"
import { AdminUsersList } from "@/components/admin/users-list.jsx"
import { AdminRolesList } from "@/components/admin/roles-list.jsx"
import { AdminSystemSettings } from "@/components/admin/system-settings.jsx"
import { AdminBackupsList } from "@/components/admin/backups-list.jsx"

export default function AdminPage() {
  const [systemStatus, setSystemStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function loadSystemStatus() {
      try {
        setLoading(true)
        const res = await apiClient.get("/api/system/status")
        setSystemStatus(res.data)
      } catch (err) {
        console.error("[v0] Error fetching system status:", err)
        setError("Failed to load system status")
      } finally {
        setLoading(false)
      }
    }
    loadSystemStatus()
  }, [])

  return (
    <PageLayout
      title="Admin Dashboard"
      description="Manage users, roles, system configuration, and backups"
      showBackButton={true}
    >
      {error && (
        <Card className="border-destructive mb-6">
          <CardContent className="flex items-center gap-3 py-4">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <p className="text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {systemStatus && (
        <div className="grid gap-4 md:grid-cols-4 mb-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemStatus.activeUsers || 0}</div>
              <p className="text-xs text-muted-foreground">Currently online</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Total Connections</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemStatus.totalConnections || 0}</div>
              <p className="text-xs text-muted-foreground">API integrations</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">System Health</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                <Badge variant={systemStatus.health === "healthy" ? "default" : "destructive"}>
                  {systemStatus.health || "Unknown"}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">Overall status</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Uptime</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemStatus.uptime || "--"}</div>
              <p className="text-xs text-muted-foreground">Days running</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="users" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="users" className="gap-2">
            <Users className="h-4 w-4" />
            <span className="hidden sm:inline">Users</span>
          </TabsTrigger>
          <TabsTrigger value="roles" className="gap-2">
            <Shield className="h-4 w-4" />
            <span className="hidden sm:inline">Roles</span>
          </TabsTrigger>
          <TabsTrigger value="settings" className="gap-2">
            <Settings className="h-4 w-4" />
            <span className="hidden sm:inline">Settings</span>
          </TabsTrigger>
          <TabsTrigger value="backups" className="gap-2">
            <HardDrive className="h-4 w-4" />
            <span className="hidden sm:inline">Backups</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="users" className="mt-6">
          <AdminUsersList />
        </TabsContent>

        <TabsContent value="roles" className="mt-6">
          <AdminRolesList />
        </TabsContent>

        <TabsContent value="settings" className="mt-6">
          <AdminSystemSettings />
        </TabsContent>

        <TabsContent value="backups" className="mt-6">
          <AdminBackupsList />
        </TabsContent>
      </Tabs>
    </PageLayout>
  )
}
