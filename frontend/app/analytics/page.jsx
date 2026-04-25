"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { PageLayout } from "@/components/ui/page-layout"
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { AlertCircle, TrendingUp, Activity, Clock, Zap, CheckCircle2, Loader2, BarChart3, HardDrive, LineChart as LineChartIcon } from "lucide-react"
import apiClient from "../../services/apiClient.js"

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadAnalytics()
  }, [])

  async function loadAnalytics() {
    try {
      setLoading(true)
      const res = await apiClient.get("/api/analytics")
      console.log("[Analytics] API Response:", res)
      // Handle both res.data (normal) and res directly (from cache)
      const data = res.data?.summary ? res.data : res
      setAnalytics(data)
      console.log("[Analytics] Processed data:", data)
    } catch (err) {
      console.error("[Analytics] Error fetching analytics:", err)
      setError("Failed to load analytics")
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <PageLayout
        title="Analytics"
        description="System performance and usage analytics"
        showBackButton={true}
      >
        <div className="grid gap-4 md:grid-cols-4 mb-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="pb-3">
                <div className="h-4 w-24 bg-muted rounded" />
              </CardHeader>
              <CardContent>
                <div className="h-8 w-16 bg-muted rounded mb-2" />
                <div className="h-3 w-20 bg-muted rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card className="flex items-center justify-center py-16">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-3" />
            <p className="text-muted-foreground">Loading analytics...</p>
          </div>
        </Card>
      </PageLayout>
    )
  }

  if (error || !analytics) {
    return (
      <PageLayout title="Analytics" description="System performance and usage analytics" showBackButton={true}>
        <Card className="border-red-200 bg-gradient-to-br from-red-50 to-red-100/50">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="flex items-center justify-center w-12 h-12 rounded-full bg-red-100 mb-4">
              <AlertCircle className="h-6 w-6 text-red-600" />
            </div>
            <h3 className="text-lg font-semibold text-red-900 mb-2">Error loading analytics</h3>
            <p className="text-red-700 text-center max-w-md">{error || "Failed to load analytics"}</p>
          </CardContent>
        </Card>
      </PageLayout>
    )
  }

  const COLORS = ["hsl(var(--chart-1))", "hsl(var(--chart-2))", "hsl(var(--chart-3))", "hsl(var(--chart-4))"]

  // Custom color palettes for pie charts
  const purpleColors = ["#a855f7", "#d946ef", "#ec4899", "#f43f5e", "#f97316"]
  const roseColors = ["#f43f5e", "#fb7185", "#fda4af", "#fecdd3", "#fee2e2"]

  return (
    <PageLayout title="Analytics" description="System performance and usage analytics" showBackButton={true} icon={<div className="p-2 bg-gradient-to-br from-blue-100 to-blue-50 rounded-lg"><LineChartIcon className="h-6 w-6 text-blue-600" /></div>}>
      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {/* Total Runs Card */}
        <Card className="group bg-gradient-to-br from-blue-50 to-blue-100/50 border-blue-200 hover:shadow-lg transition-all duration-200 overflow-hidden">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between mb-2">
              <CardTitle className="text-sm font-medium text-slate-700">Total Runs</CardTitle>
              <div className="p-2 bg-blue-100 rounded-lg">
                <Zap className="h-4 w-4 text-blue-600" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl lg:text-4xl font-bold text-blue-900">{analytics.summary?.totalRuns || 0}</div>
            <p className="text-xs text-blue-700 mt-1">All time</p>
          </CardContent>
        </Card>

        {/* Success Rate Card */}
        <Card className="group bg-gradient-to-br from-green-50 to-green-100/50 border-green-200 hover:shadow-lg transition-all duration-200 overflow-hidden">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between mb-2">
              <CardTitle className="text-sm font-medium text-slate-700">Success Rate</CardTitle>
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl lg:text-4xl font-bold text-green-900">{(analytics.summary?.successRate || 0).toFixed(2)}%</div>
            <p className="text-xs text-green-700 mt-1">Last 30 days</p>
          </CardContent>
        </Card>

        {/* Average Response Time Card */}
        <Card className="group bg-gradient-to-br from-purple-50 to-purple-100/50 border-purple-200 hover:shadow-lg transition-all duration-200 overflow-hidden">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between mb-2">
              <CardTitle className="text-sm font-medium text-slate-700">Avg Response Time</CardTitle>
              <div className="p-2 bg-purple-100 rounded-lg">
                <Clock className="h-4 w-4 text-purple-600" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl lg:text-4xl font-bold text-purple-900">{analytics.summary?.avgResponseTime || 0}ms</div>
            <p className="text-xs text-purple-700 mt-1">Average</p>
          </CardContent>
        </Card>

        {/* Runs Last 24h Card */}
        <Card className="group bg-gradient-to-br from-rose-50 to-rose-100/50 border-rose-200 hover:shadow-lg transition-all duration-200 overflow-hidden">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between mb-2">
              <CardTitle className="text-sm font-medium text-slate-700">Runs Last 24h</CardTitle>
              <div className="p-2 bg-rose-100 rounded-lg">
                <Activity className="h-4 w-4 text-rose-600" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl lg:text-4xl font-bold text-rose-900">{analytics.summary?.runsLast24h || 0}</div>
            <p className="text-xs text-rose-700 mt-1">Last 24 hours</p>
          </CardContent>
        </Card>


      </div>

      {/* Tabs */}
      <Tabs defaultValue="performance" className="w-full">
        <TabsList className="grid w-full grid-cols-2 mb-8 bg-gradient-to-r from-slate-100 to-slate-50 border border-slate-200 rounded-lg p-1">
          <TabsTrigger value="performance" className="gap-2 data-[state=active]:bg-gradient-to-br data-[state=active]:from-blue-50 data-[state=active]:to-blue-100 data-[state=active]:text-blue-700 data-[state=active]:shadow-sm">
            <TrendingUp className="h-4 w-4" />
            <span className="hidden sm:inline font-medium">Performance</span>
          </TabsTrigger>
          <TabsTrigger value="trends" className="gap-2 data-[state=active]:bg-gradient-to-br data-[state=active]:from-orange-50 data-[state=active]:to-orange-100 data-[state=active]:text-orange-700 data-[state=active]:shadow-sm">
            <BarChart3 className="h-4 w-4" />
            <span className="hidden sm:inline font-medium">Trends</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="mt-6 space-y-6">
          <Card className="group bg-gradient-to-br from-blue-50 via-white to-slate-50/30 border-blue-200 shadow-sm hover:shadow-lg hover:border-blue-300 transition-all duration-300">
            <CardHeader className="pb-4 border-b border-blue-100/50">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-blue-900 flex items-center gap-2">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <TrendingUp className="h-4 w-4 text-blue-600" />
                    </div>
                    Success Rate History
                  </CardTitle>
                  <CardDescription className="text-blue-600/70 mt-1">Success rate over the last 30 days</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <ChartContainer
                config={{
                  successRate: {
                    label: "Success Rate (%)",
                    color: "#3b82f6",
                  },
                }}
                className="h-[300px] w-full"
              >
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={analytics.successRateHistory && Array.isArray(analytics.successRateHistory) ? analytics.successRateHistory : []} margin={{ top: 10, right: 30, left: 0, bottom: 40 }}>
                    <defs>
                      <linearGradient id="colorSuccess" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                    <YAxis stroke="#64748b" fontSize={12} domain={[0, 100]} />
                    <ChartTooltip content={<ChartTooltipContent />} cursor={{ stroke: '#3b82f6', strokeWidth: 2 }} />
                    <Legend wrapperStyle={{ paddingTop: '20px' }} />
                    <Line type="monotone" dataKey="successRate" stroke="#3b82f6" strokeWidth={3} dot={{ fill: '#3b82f6', r: 5 }} activeDot={{ r: 7 }} />
                  </LineChart>
                </ResponsiveContainer>
              </ChartContainer>
            </CardContent>
          </Card>

        </TabsContent>

        <TabsContent value="trends" className="mt-6 space-y-6">
          <Card className="group bg-gradient-to-br from-amber-50 via-white to-slate-50/30 border-amber-200 shadow-sm hover:shadow-lg hover:border-amber-300 transition-all duration-300">
            <CardHeader className="pb-4 border-b border-amber-100/50">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-amber-900 flex items-center gap-2">
                    <div className="p-2 bg-amber-100 rounded-lg">
                      <Activity className="h-4 w-4 text-amber-600" />
                    </div>
                    Daily Activity
                  </CardTitle>
                  <CardDescription className="text-amber-600/70 mt-1">Runs per day over the last 30 days</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <ChartContainer
                config={{
                  runs: {
                    label: "Runs",
                    color: "#f59e0b",
                  },
                }}
                className="h-[400px] w-full"
              >
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.dailyActivity && Array.isArray(analytics.dailyActivity) ? analytics.dailyActivity : []} margin={{ top: 10, right: 30, left: 0, bottom: 40 }}>
                    <defs>
                      <linearGradient id="colorActivity" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8} />
                        <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.4} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                    <YAxis stroke="#64748b" fontSize={12} />
                    <ChartTooltip content={<ChartTooltipContent />} cursor={{ fill: '#f59e0b', fillOpacity: 0.1 }} />
                    <Legend wrapperStyle={{ paddingTop: '20px' }} />
                    <Bar dataKey="runs" fill="url(#colorActivity)" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartContainer>
            </CardContent>
          </Card>

          <div className="grid gap-6 md:grid-cols-2">
            {/* Runs by Connection Card */}
            <Card className="group bg-gradient-to-br from-purple-50 via-white to-slate-50/30 border-purple-200 shadow-sm hover:shadow-lg hover:border-purple-300 transition-all duration-300">
              <CardHeader className="pb-4 border-b border-purple-100/50">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-purple-900 flex items-center gap-2">
                      <div className="p-2 bg-purple-100 rounded-lg">
                        <BarChart3 className="h-4 w-4 text-purple-600" />
                      </div>
                      Runs by Connection
                    </CardTitle>
                    <CardDescription className="text-purple-600/70 mt-1">Distribution of runs across connections</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                <ChartContainer
                  config={{
                    runs: {
                      label: "Runs",
                      color: "#a855f7",
                    },
                  }}
                  className="h-[300px] w-full"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={analytics.runsByConnection && Array.isArray(analytics.runsByConnection) ? analytics.runsByConnection : []}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value }) => `${name}: ${value}`}
                        outerRadius={80}
                        fill="#a855f7"
                        dataKey="value"
                      >
                        {(analytics.runsByConnection && Array.isArray(analytics.runsByConnection) ? analytics.runsByConnection : []).map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={purpleColors[index % purpleColors.length]} />
                        ))}
                      </Pie>
                      <ChartTooltip content={<ChartTooltipContent />} cursor={{ fill: 'rgba(168, 85, 247, 0.05)' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </CardContent>
            </Card>

            {/* Status Distribution Card */}
            <Card className="group bg-gradient-to-br from-rose-50 via-white to-slate-50/30 border-rose-200 shadow-sm hover:shadow-lg hover:border-rose-300 transition-all duration-300">
              <CardHeader className="pb-4 border-b border-rose-100/50">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-rose-900 flex items-center gap-2">
                      <div className="p-2 bg-rose-100 rounded-lg">
                        <TrendingUp className="h-4 w-4 text-rose-600" />
                      </div>
                      Status Distribution
                    </CardTitle>
                    <CardDescription className="text-rose-600/70 mt-1">Run outcomes breakdown</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                <ChartContainer
                  config={{
                    count: {
                      label: "Count",
                      color: "#f43f5e",
                    },
                  }}
                  className="h-[300px] w-full"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={analytics.statusDistribution && Array.isArray(analytics.statusDistribution) ? analytics.statusDistribution : []}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value }) => `${name}: ${value}`}
                        outerRadius={80}
                        fill="#f43f5e"
                        dataKey="value"
                      >
                        {(analytics.statusDistribution && Array.isArray(analytics.statusDistribution) ? analytics.statusDistribution : []).map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={roseColors[index % roseColors.length]} />
                        ))}
                      </Pie>
                      <ChartTooltip content={<ChartTooltipContent />} cursor={{ fill: 'rgba(244, 63, 94, 0.05)' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </PageLayout>
  )
}
