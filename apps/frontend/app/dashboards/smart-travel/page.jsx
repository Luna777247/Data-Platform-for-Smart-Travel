'use client'

import SmartTravelDashboard from '@/components/dashboard/smart-travel-dashboard'
import { PageLayout } from '@/components/ui/page-layout'
import { MapPin } from 'lucide-react'

export default function SmartTravelDashboardPage() {
  return (
    <PageLayout
      title="Smart Travel Dashboard"
      description="Analyze data from Places collection - MongoDB Atlas"
      showBackButton={true}
      icon={<div className="p-2 bg-gradient-to-br from-rose-100 to-rose-50 rounded-lg"><MapPin className="h-6 w-6 text-rose-600" /></div>}
    >
      <SmartTravelDashboard />
    </PageLayout>
  )
}
