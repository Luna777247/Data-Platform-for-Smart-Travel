"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
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
import { Play, Pause, Clock, AlertCircle } from "lucide-react"
import apiClient from "../../services/apiClient.js"

export function AirflowDAGsList({ searchTerm, onStatsUpdate }) {
  const [dags, setDAGs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [actioningId, setActioningId] = useState(null)

  useEffect(() => {
    loadDAGs()
  }, [])

  async function loadDAGs() {
    try {
      setLoading(true)
      const res = await apiClient.get("/api/airflow/dags")
      setDAGs(res.data || [])
    } catch (err) {
      console.error("[v0] Error fetching DAGs:", err)
      setError("Failed to load DAGs")
    } finally {
      setLoading(false)
    }
  }

  const triggerDAG = async (dagId) => {
    setActioningId(dagId)
    try {
      await apiClient.post(`/api/airflow/dags/${dagId}/trigger`, {})
      loadDAGs()
      onStatsUpdate?.()
    } catch (err) {
      console.error("[v0] Error triggering DAG:", err)
      setError("Failed to trigger DAG")
    } finally {
      setActioningId(null)
    }
  }

  const pauseDAG = async (dagId) => {
    setActioningId(dagId)
    try {
      await apiClient.post(`/api/airflow/dags/${dagId}/pause`, {})
      loadDAGs()
      onStatsUpdate?.()
    } catch (err) {
      console.error("[v0] Error pausing DAG:", err)
      setError("Failed to pause DAG")
    } finally {
      setActioningId(null)
    }
  }

  const resumeDAG = async (dagId) => {
    setActioningId(dagId)
    try {
      await apiClient.post(`/api/airflow/dags/${dagId}/resume`, {})
      loadDAGs()
      onStatsUpdate?.()
    } catch (err) {
      console.error("[v0] Error resuming DAG:", err)
      setError("Failed to resume DAG")
    } finally {
      setActioningId(null)
    }
  }

  const filteredDAGs = dags.filter(
    (dag) =>
      dag.dagId?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      dag.description?.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <div className="space-y-4">
      {error && (
        <Card className="border-destructive">
          <CardContent className="flex items-center gap-3 py-4">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <p className="text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>DAGs</CardTitle>
          <CardDescription>Manage and monitor Airflow DAGs</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading DAGs...</div>
          ) : filteredDAGs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">No DAGs found</div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>DAG ID</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Last Run</TableHead>
                    <TableHead>Next Run</TableHead>
                    <TableHead>Success Rate</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredDAGs.map((dag) => (
                    <TableRow key={dag.dagId}>
                      <TableCell className="font-medium">{dag.dagId}</TableCell>
                      <TableCell>
                        <Badge variant={dag.isPaused ? "secondary" : dag.isActive ? "default" : "outline"}>
                          {dag.isPaused ? "Paused" : dag.isActive ? "Active" : "Inactive"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {dag.lastRun ? new Date(dag.lastRun).toLocaleString() : "Never"}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {dag.nextRun ? new Date(dag.nextRun).toLocaleString() : "N/A"}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{dag.successRate || 0}%</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button variant="ghost" size="sm" disabled={actioningId === dag.dagId} className="gap-1">
                                {actioningId === dag.dagId ? (
                                  <Clock className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Play className="h-4 w-4" />
                                )}
                                <span className="hidden sm:inline">Trigger</span>
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Trigger DAG?</AlertDialogTitle>
                                <AlertDialogDescription>
                                  This will start a new run of the {dag.dagId} DAG.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction onClick={() => triggerDAG(dag.dagId)}>Trigger</AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>

                          {dag.isPaused ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => resumeDAG(dag.dagId)}
                              disabled={actioningId === dag.dagId}
                              className="gap-1"
                            >
                              {actioningId === dag.dagId ? (
                                <Clock className="h-4 w-4 animate-spin" />
                              ) : (
                                <Play className="h-4 w-4" />
                              )}
                              <span className="hidden sm:inline">Resume</span>
                            </Button>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => pauseDAG(dag.dagId)}
                              disabled={actioningId === dag.dagId}
                              className="gap-1"
                            >
                              {actioningId === dag.dagId ? (
                                <Clock className="h-4 w-4 animate-spin" />
                              ) : (
                                <Pause className="h-4 w-4" />
                              )}
                              <span className="hidden sm:inline">Pause</span>
                            </Button>
                          )}
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
