"use client"

import { useEffect, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { PageLayout } from "@/components/ui/page-layout"
import { AlertCircle, Clock, Activity } from "lucide-react"
import apiClient from "../../services/apiClient.js"
import { AirflowDAGsList } from "@/components/airflow/dags-list.jsx"
import { AirflowRunsHistory } from "@/components/airflow/runs-history.jsx"
import { AirflowStatsPanel } from "@/components/airflow/stats-panel.jsx"

export default function AirflowPage() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState("")

  useEffect(() => {
    loadStats()
  }, [])

  async function loadStats() {
    try {
      setLoading(true)
      const res = await apiClient.get("/api/airflow/stats")
      setStats(res.data)
    } catch (err) {
      console.error("[v0] Error fetching Airflow stats:", err)
      setError("Failed to load Airflow statistics")
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageLayout
      title="Airflow Scheduling"
      description="Manage DAGs, triggers, and monitor pipeline execution"
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

      {stats && <AirflowStatsPanel stats={stats} />}

      <Tabs defaultValue="dags" className="w-full mt-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="dags" className="gap-2">
            <Activity className="h-4 w-4" />
            <span className="hidden sm:inline">DAGs</span>
          </TabsTrigger>
          <TabsTrigger value="runs" className="gap-2">
            <Clock className="h-4 w-4" />
            <span className="hidden sm:inline">Runs</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dags" className="mt-6">
          <div className="mb-4">
            <Input
              placeholder="Search DAGs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="max-w-sm"
            />
          </div>
          <AirflowDAGsList searchTerm={searchTerm} onStatsUpdate={loadStats} />
        </TabsContent>

        <TabsContent value="runs" className="mt-6">
          <AirflowRunsHistory />
        </TabsContent>
      </Tabs>
    </PageLayout>
  )
}
