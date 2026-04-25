"use client"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Calendar, Clock, Play, Pause, Trash2, Edit2, Plus, Loader2, AlertCircle, Search, Filter, CheckCircle, XCircle, RotateCcw } from "lucide-react"
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
import { PageLayout } from "@/components/ui/page-layout"
import apiClient from "../../services/apiClient.js"
import { ScheduleFormDialog } from "@/components/schedules/schedule-form-dialog.jsx"

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [filterStatus, setFilterStatus] = useState("all")
  const [actioningId, setActioningId] = useState(null)
  const [editingSchedule, setEditingSchedule] = useState(null)

  useEffect(() => {
    fetchSchedules()
  }, [])

  async function fetchSchedules() {
    try {
      setLoading(true)
      const response = await apiClient.get("/api/schedules")
      const data = response.data
      const mappedData = (data || []).map((schedule) => ({
        ...schedule,
        id: schedule._id || schedule.id,
      }))
      setSchedules(mappedData)
    } catch (err) {
      console.error("[v0] Error fetching schedules:", err)
      setError(err instanceof Error ? err.message : "Failed to load schedules")
    } finally {
      setLoading(false)
    }
  }

  const toggleScheduleStatus = async (scheduleId, currentStatus) => {
    setActioningId(scheduleId)
    const newStatus = !currentStatus
    try {
      await apiClient.put(`/api/schedules/${scheduleId}`, {
        isActive: newStatus,
      })
      
      // Update the local state immediately
      setSchedules(prevSchedules => 
        prevSchedules.map(schedule => 
          schedule.id === scheduleId 
            ? { ...schedule, isActive: newStatus } 
            : schedule
        )
      )
    } catch (err) {
      console.error("[v0] Error updating schedule status:", err)
      setError(`Failed to ${newStatus ? 'resume' : 'pause'} schedule`)
    } finally {
      setActioningId(null)
    }
  }

  // For backward compatibility
  const pauseSchedule = (scheduleId) => toggleScheduleStatus(scheduleId, true)
  const resumeSchedule = (scheduleId) => toggleScheduleStatus(scheduleId, false)

  const deleteSchedule = async (scheduleId) => {
    setActioningId(scheduleId)
    try {
      await apiClient.delete(`/api/schedules/${scheduleId}`)
      setSchedules(schedules.filter((s) => s.id !== scheduleId))
    } catch (err) {
      console.error("[v0] Error deleting schedule:", err)
      setError("Failed to delete schedule")
    } finally {
      setActioningId(null)
    }
  }

  const filteredSchedules = schedules.filter(
    (s) =>
      (s.connectionName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.description?.toLowerCase().includes(searchTerm.toLowerCase())) &&
      (filterStatus === "all" ? true : filterStatus === "active" ? s.isActive : !s.isActive)
  )

  if (loading) {
    return (
      <PageLayout
        title="Schedules"
        description="Manage automated API runs and schedules"
        showBackButton={true}
        headerActions={
          <ScheduleFormDialog
            schedule={null}
            onSave={fetchSchedules}
            trigger={
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                Create Schedule
              </Button>
            }
          />
        }
      >
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Loading schedules...</span>
        </div>
      </PageLayout>
    )
  }

  return (
    <PageLayout
      title="Schedules"
      description="Manage automated API runs and schedules"
      showBackButton={true}
      icon={<div className="p-2 bg-gradient-to-br from-purple-100 to-purple-50 rounded-lg"><Calendar className="h-6 w-6 text-purple-600" /></div>}
      headerActions={
        <ScheduleFormDialog
          schedule={null}
          onSave={() => {
            fetchSchedules()
          }}
          trigger={
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              Create Schedule
            </Button>
          }
        />
      }
    >
      {/* Edit Schedule Dialog - Only rendered when editingSchedule has a value */}
      <ScheduleFormDialog
        key={editingSchedule?.id || 'create'}
        schedule={editingSchedule}
        onSave={(savedSchedule) => {
          // Use functional update to ensure we have the latest state
          setSchedules(prevSchedules => {
            const scheduleId = savedSchedule.id || savedSchedule._id;
            const existingIndex = prevSchedules.findIndex(s => s.id === scheduleId);
            
            if (existingIndex >= 0) {
              // Update existing schedule using immutable update pattern
              return [
                ...prevSchedules.slice(0, existingIndex),
                { ...prevSchedules[existingIndex], ...savedSchedule },
                ...prevSchedules.slice(existingIndex + 1)
              ];
            } else {
              // Add new schedule
              return [...prevSchedules, { 
                ...savedSchedule, 
                id: scheduleId 
              }];
            }
          });
          setEditingSchedule(null);
        }}
        open={!!editingSchedule}
        onOpenChange={(open) => {
          if (!open) {
            setEditingSchedule(null)
          }
        }}
      />
      {error && (
        <Card className="border-destructive mb-6">
          <CardContent className="flex items-center gap-3 py-4">
            <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0" />
            <p className="text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Search and Filter Bar */}
      {!loading && filteredSchedules.length > 0 && (
        <div className="flex flex-col lg:flex-row gap-4 mb-6 p-4 bg-gradient-to-r from-slate-50 to-slate-100 rounded-lg border">
          <div className="relative flex-1 min-w-0">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground flex-shrink-0" />
            <Input
              placeholder="Search schedules..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4"
            />
          </div>
          <div className="flex flex-wrap gap-2 justify-center lg:justify-start">
            <Button
              variant={filterStatus === "all" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilterStatus("all")}
              className="gap-2 flex-shrink-0"
            >
              <Filter className="h-4 w-4" />
              <span className="hidden sm:inline">All ({schedules.length})</span>
              <span className="sm:hidden">{schedules.length}</span>
            </Button>
            <Button
              variant={filterStatus === "active" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilterStatus("active")}
              className="gap-2 flex-shrink-0"
            >
              <RotateCcw className="h-4 w-4" />
              <span className="hidden sm:inline">Active ({schedules.filter(s => s.isActive).length})</span>
              <span className="sm:hidden">{schedules.filter(s => s.isActive).length}</span>
            </Button>
            <Button
              variant={filterStatus === "paused" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilterStatus("paused")}
              className="gap-2 flex-shrink-0"
            >
              <Pause className="h-4 w-4" />
              <span className="hidden sm:inline">Paused ({schedules.filter(s => !s.isActive).length})</span>
              <span className="sm:hidden">{schedules.filter(s => !s.isActive).length}</span>
            </Button>
          </div>
        </div>
      )}

      {filteredSchedules.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Calendar className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No schedules configured</h3>
            <p className="text-muted-foreground text-center mb-4 text-pretty max-w-md">
              Create a schedule to automate your API runs
            </p>
            <ScheduleFormDialog schedule={null} onSave={fetchSchedules} trigger={<Button>Create Schedule</Button>} />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredSchedules.map((schedule, index) => (
            <Card key={`${schedule.id}-${index}`} className="group hover:shadow-lg transition-all duration-200 border-l-4 border-l-blue-500 hover:border-l-purple-500 overflow-hidden">
              <CardHeader className="pb-3">
                <div className="flex flex-col gap-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2 flex-wrap">
                        <CardTitle className="text-lg truncate group-hover:text-blue-600 transition-colors">
                          {schedule.connectionName}
                        </CardTitle>
                        <div className="flex gap-2 flex-wrap">
                          <Badge variant={schedule.isActive ? "default" : "secondary"} className={schedule.isActive ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}>
                            {schedule.isActive ? (
                              <>
                                <RotateCcw className="h-3 w-3 mr-1 flex-shrink-0" />
                                Active
                              </>
                            ) : (
                              <>
                                <Pause className="h-3 w-3 mr-1 flex-shrink-0" />
                                Paused
                              </>
                            )}
                          </Badge>
                          <Badge variant="outline" className="hidden sm:inline-flex gap-1">
                            <Calendar className="h-3 w-3" />
                            {schedule.scheduleType}
                          </Badge>
                        </div>
                      </div>
                      <CardDescription className="line-clamp-1">
                        <code className="text-xs bg-muted px-2 py-1 rounded inline-block">{schedule.cronExpression}</code>
                      </CardDescription>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-4">
                  <div className="grid gap-3 grid-cols-2 sm:grid-cols-4 flex-1">
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-blue-500 flex-shrink-0" />
                      <div className="min-w-0">
                        <p className="text-xs text-muted-foreground">Next Run</p>
                        <p className="text-sm font-medium truncate">
                          {schedule.nextRun ? new Date(schedule.nextRun).toLocaleString() : "Never"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-purple-500 flex-shrink-0" />
                      <div className="min-w-0">
                        <p className="text-xs text-muted-foreground">Last Run</p>
                        <p className="text-sm font-medium truncate">
                          {schedule.lastRun ? new Date(schedule.lastRun).toLocaleString() : "Never"}
                        </p>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Status</p>
                      <Badge variant={schedule.lastStatus === "success" ? "default" : "destructive"} className={schedule.lastStatus === "success" ? "bg-green-100 text-green-800 gap-1" : "gap-1"}>
                        {schedule.lastStatus === "success" ? (
                          <>
                            <CheckCircle className="h-3 w-3" />
                            Success
                          </>
                        ) : (
                          <>
                            <XCircle className="h-3 w-3" />
                            {schedule.lastStatus}
                          </>
                        )}
                      </Badge>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Runs</p>
                      <p className="text-sm font-medium mt-1">{schedule.totalRuns}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0 sm:flex-col">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => (schedule.isActive ? pauseSchedule(schedule.id) : resumeSchedule(schedule.id))}
                      disabled={actioningId === schedule.id}
                      className="gap-2 flex-1 sm:flex-none sm:w-full"
                    >
                      {actioningId === schedule.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : schedule.isActive ? (
                        <Pause className="h-4 w-4" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                      <span className="hidden sm:inline">{schedule.isActive ? "Pause" : "Resume"}</span>
                    </Button>
                    <Button 
                      variant="outline"
                      size="sm" 
                      onClick={(e) => {
                        e.stopPropagation()
                        setEditingSchedule(schedule)
                      }}
                      className="gap-2 flex-1 sm:flex-none sm:w-full"
                    >
                      <Edit2 className="h-4 w-4" />
                      <span className="hidden sm:inline">Edit</span>
                    </Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="outline" size="sm" className="text-destructive gap-2 flex-1 sm:flex-none sm:w-full">
                          {actioningId === schedule.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                          <span className="hidden sm:inline">Delete</span>
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle className="flex items-center gap-2">
                            <Trash2 className="h-5 w-5 text-destructive" />
                            Delete schedule?
                          </AlertDialogTitle>
                          <AlertDialogDescription>
                            This action cannot be undone. The schedule "{schedule.connectionName}" will be permanently
                            deleted.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction onClick={() => deleteSchedule(schedule.id)} className="bg-destructive hover:bg-destructive/90">Delete</AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </PageLayout>
  )
}
