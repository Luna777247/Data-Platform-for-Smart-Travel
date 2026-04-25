"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
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
import { HardDrive, Download, RotateCcw, Plus, Trash2, Clock } from "lucide-react"
import apiClient from "../../services/apiClient.js"

export function AdminBackupsList() {
  const [backups, setBackups] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [creatingBackup, setCreatingBackup] = useState(false)
  const [restoringId, setRestoringId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    loadBackups()
  }, [])

  async function loadBackups() {
    try {
      setLoading(true)
      const res = await apiClient.get("/api/backups")
      setBackups(res.data || [])
    } catch (err) {
      console.error("[v0] Error fetching backups:", err)
      setError("Failed to load backups")
    } finally {
      setLoading(false)
    }
  }

  const createBackup = async () => {
    setCreatingBackup(true)
    try {
      const res = await apiClient.post("/api/backups", {})
      setBackups([res.data, ...backups])
    } catch (err) {
      console.error("[v0] Error creating backup:", err)
      setError("Failed to create backup")
    } finally {
      setCreatingBackup(false)
    }
  }

  const restoreBackup = async (backupId) => {
    setRestoringId(backupId)
    try {
      await apiClient.post(`/api/backups/${backupId}/restore`, {})
      setError(null)
    } catch (err) {
      console.error("[v0] Error restoring backup:", err)
      setError("Failed to restore backup")
    } finally {
      setRestoringId(null)
    }
  }

  const deleteBackup = async (backupId) => {
    setDeletingId(backupId)
    try {
      await apiClient.delete(`/api/backups/${backupId}`)
      setBackups(backups.filter((b) => b.id !== backupId))
    } catch (err) {
      console.error("[v0] Error deleting backup:", err)
      setError("Failed to delete backup")
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Backups</h3>
          <p className="text-sm text-muted-foreground">Manage system backups and restore points</p>
        </div>
        <Button onClick={createBackup} disabled={creatingBackup} className="gap-2">
          {creatingBackup ? <Clock className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          Create Backup
        </Button>
      </div>

      {error && (
        <Card className="border-destructive">
          <CardContent className="py-4 text-sm text-destructive">{error}</CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="pt-6">
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading backups...</div>
          ) : backups.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <HardDrive className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-4">No backups found</p>
              <Button onClick={createBackup} className="gap-2">
                <Plus className="h-4 w-4" />
                Create First Backup
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Backup Name</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {backups.map((backup) => (
                    <TableRow key={backup.id}>
                      <TableCell className="font-medium">{backup.name}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {(backup.size / 1024 / 1024).toFixed(2)} MB
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(backup.createdAt).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Badge variant={backup.status === "completed" ? "default" : "secondary"}>{backup.status}</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button variant="ghost" size="sm" className="gap-1">
                            <Download className="h-4 w-4" />
                            <span className="hidden sm:inline">Download</span>
                          </Button>
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button variant="ghost" size="sm" className="gap-1">
                                <RotateCcw className="h-4 w-4" />
                                <span className="hidden sm:inline">Restore</span>
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Restore backup?</AlertDialogTitle>
                                <AlertDialogDescription>
                                  This will restore the system to the state of this backup. Current data will be
                                  overwritten.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction onClick={() => restoreBackup(backup.id)}>
                                  {restoringId === backup.id ? "Restoring..." : "Restore"}
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button variant="ghost" size="sm" className="text-destructive">
                                {deletingId === backup.id ? (
                                  <Clock className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Trash2 className="h-4 w-4" />
                                )}
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Delete backup?</AlertDialogTitle>
                                <AlertDialogDescription>
                                  This backup will be permanently deleted.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction onClick={() => deleteBackup(backup.id)}>Delete</AlertDialogAction>
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
    </div>
  )
}
