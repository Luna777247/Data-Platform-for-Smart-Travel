"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { PageLayout } from "@/components/ui/page-layout"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend, ResponsiveContainer } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Download, Edit2, RefreshCw } from "lucide-react"
import apiClient from "../../../services/apiClient.js"

export default function ReportDetailPage() {
  const params = useParams()
  const reportId = params.id
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    loadReport()
  }, [reportId])

  async function loadReport() {
    try {
      setLoading(true)
      const res = await apiClient.get(`/api/reports/${reportId}`)
      setReport(res.data)
    } catch (err) {
      console.error("[v0] Error fetching report:", err)
      setError("Failed to load report")
    } finally {
      setLoading(false)
    }
  }

  const refreshReport = async () => {
    setRefreshing(true)
    try {
      const res = await apiClient.post(`/api/reports/${reportId}/refresh`, {})
      setReport(res.data)
    } catch (err) {
      console.error("[v0] Error refreshing report:", err)
      setError("Failed to refresh report")
    } finally {
      setRefreshing(false)
    }
  }

  if (loading) {
    return <PageLayout title="Loading..." showBackButton={true}></PageLayout>
  }

  if (error || !report) {
    return (
      <PageLayout title="Report Not Found" showBackButton={true}>
        <Card className="border-destructive">
          <CardContent className="py-8 text-center">
            <p className="text-destructive mb-4">{error || "Report not found"}</p>
            <Link href="/reports">
              <Button>Back to Reports</Button>
            </Link>
          </CardContent>
        </Card>
      </PageLayout>
    )
  }

  return (
    <PageLayout
      title={report.name}
      description={report.description}
      showBackButton={true}
      headerActions={
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={refreshReport}
            disabled={refreshing}
            className="gap-2 bg-transparent"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          <Button variant="outline" size="sm" className="gap-2 bg-transparent">
            <Download className="h-4 w-4" />
            Export
          </Button>
          <Link href={`/reports/${reportId}/edit`}>
            <Button size="sm" className="gap-2">
              <Edit2 className="h-4 w-4" />
              Edit
            </Button>
          </Link>
        </div>
      }
    >
      <div className="grid gap-4 md:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Type</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge>{report.type}</Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={report.status === "active" ? "default" : "secondary"}>{report.status}</Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Schedule</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{report.schedule}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Last Run</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{report.lastRun ? new Date(report.lastRun).toLocaleDateString() : "Never"}</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          {report.includeCharts && <TabsTrigger value="charts">Charts</TabsTrigger>}
          {report.includeTables && <TabsTrigger value="tables">Tables</TabsTrigger>}
          {report.includeMetrics && <TabsTrigger value="metrics">Metrics</TabsTrigger>}
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Report Overview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2">Description</h4>
                <p className="text-muted-foreground">{report.description || "No description provided"}</p>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Data Source</h4>
                <p className="text-muted-foreground">{report.dataSource}</p>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Created</h4>
                <p className="text-muted-foreground">{new Date(report.createdAt).toLocaleString()}</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {report.includeCharts && (
          <TabsContent value="charts" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Report Charts</CardTitle>
              </CardHeader>
              <CardContent>
                <ChartContainer
                  config={{
                    value: {
                      label: "Value",
                      color: "hsl(var(--chart-1))",
                    },
                  }}
                  className="h-[400px]"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={report.chartData || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Legend />
                      <Bar dataKey="value" fill="var(--color-value)" />
                    </BarChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {report.includeTables && (
          <TabsContent value="tables" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Report Data</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Column 1</TableHead>
                        <TableHead>Column 2</TableHead>
                        <TableHead>Column 3</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(report.tableData || []).map((row, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{row.col1}</TableCell>
                          <TableCell>{row.col2}</TableCell>
                          <TableCell>{row.col3}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {report.includeMetrics && (
          <TabsContent value="metrics" className="mt-6">
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Total Records</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{report.metrics?.totalRecords || 0}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{report.metrics?.successRate || 0}%</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{report.metrics?.avgResponseTime || 0}ms</div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        )}
      </Tabs>
    </PageLayout>
  )
}
