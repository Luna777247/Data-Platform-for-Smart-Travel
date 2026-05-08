"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function AirflowStatsPanel({ stats }) {
  return (
    <div className="grid gap-4 md:grid-cols-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Total DAGs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalDAGs || 0}</div>
          <p className="text-xs text-muted-foreground">Active pipelines</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Running</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-blue-500">{stats.runningDAGs || 0}</div>
          <p className="text-xs text-muted-foreground">Currently executing</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-500">{stats.successRate || 0}%</div>
          <p className="text-xs text-muted-foreground">Last 30 days</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Failed Runs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-red-500">{stats.failedRuns || 0}</div>
          <p className="text-xs text-muted-foreground">Needs attention</p>
        </CardContent>
      </Card>
    </div>
  )
}
