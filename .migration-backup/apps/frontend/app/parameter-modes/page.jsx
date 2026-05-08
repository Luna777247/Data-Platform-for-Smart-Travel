"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Plus, Trash2, Edit2, AlertCircle } from "lucide-react"
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
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import apiClient from "../../services/apiClient.js"
import { ParameterModeFormDialog } from "@/components/parameter-modes/parameter-mode-form-dialog.jsx"

export default function ParameterModesPage() {
  const [modes, setModes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [editingMode, setEditingMode] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    loadModes()
  }, [])

  async function loadModes() {
    try {
      setLoading(true)
      const res = await apiClient.get("/api/parameter-modes")
      setModes(res.data || [])
    } catch (err) {
      console.error("[v0] Error fetching parameter modes:", err)
      setError("Failed to load parameter modes")
    } finally {
      setLoading(false)
    }
  }

  const deleteMode = async (modeId) => {
    setDeletingId(modeId)
    try {
      await apiClient.delete(`/api/parameter-modes/${modeId}`)
      setModes(modes.filter((m) => m.id !== modeId))
    } catch (err) {
      console.error("[v0] Error deleting mode:", err)
      setError("Failed to delete parameter mode")
    } finally {
      setDeletingId(null)
    }
  }

  const filteredModes = modes.filter(
    (m) =>
      m.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.description?.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <PageLayout
      title="Parameter Modes"
      description="Manage parameter modes for API requests"
      showBackButton={true}
      headerActions={
        <ParameterModeFormDialog
          mode={editingMode}
          onSave={() => {
            setEditingMode(null)
            loadModes()
          }}
          trigger={
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              New Mode
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
          placeholder="Search parameter modes..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Parameter Modes</CardTitle>
          <CardDescription>Define how parameters are passed to API requests</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading parameter modes...</div>
          ) : filteredModes.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">No parameter modes found</div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredModes.map((mode) => (
                    <TableRow key={mode.id}>
                      <TableCell className="font-medium">{mode.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{mode.type}</Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">{mode.description}</TableCell>
                      <TableCell>
                        <Badge variant={mode.isActive ? "default" : "secondary"}>
                          {mode.isActive ? "Active" : "Inactive"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button variant="ghost" size="sm" onClick={() => setEditingMode(mode)}>
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button variant="ghost" size="sm" className="text-destructive">
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Delete parameter mode?</AlertDialogTitle>
                                <AlertDialogDescription>
                                  This action cannot be undone. The mode "{mode.name}" will be permanently deleted.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction onClick={() => deleteMode(mode.id)}>Delete</AlertDialogAction>
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
