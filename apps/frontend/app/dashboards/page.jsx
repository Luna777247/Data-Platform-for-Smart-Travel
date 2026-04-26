'use client'

import dynamic from 'next/dynamic'
import { BackToHomeButton } from "@/components/ui/back-to-home-button"

const EmbeddedDashboard = dynamic(
  () => import('@/components/dashboard/embedded-dashboard').then(mod => ({ default: mod.EmbeddedDashboard })),
  { 
    ssr: false,
    loading: () => (
      <div className="border rounded-lg p-6 animate-pulse">
        <div className="h-[800px] bg-muted rounded"></div>
      </div>
    )
  }
)

export default function DashboardsPage() {
  return (
    <div className="container mx-auto p-6 space-y-8">
      <div className="flex items-center gap-4 mb-4">
        <BackToHomeButton />
      </div>
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Analytics Dashboards</h1>
        <p className="text-muted-foreground">
          Real-time insights and visualizations powered by Google Looker Studio
        </p>
      </div>

      <EmbeddedDashboard
        reportUrl="https://lookerstudio.google.com/embed/reporting/cb87db24-90b3-47f2-a510-812cd9673172/page/TlJ0C"
        title="ETL Performance Dashboard"
        description="Monitor API runs, data quality, and system health in real-time"
        bordered={true}
        titled={true}
        theme="light"
        height="800px"
        autoRefresh={true}
        refreshInterval={300}
        showControls={true}
        fallbackToExternal={true}
      />
    </div>
  )
}
