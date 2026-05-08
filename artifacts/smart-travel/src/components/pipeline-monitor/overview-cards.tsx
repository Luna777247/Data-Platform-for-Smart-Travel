// frontendphp/components/pipeline-monitor/overview-cards.tsx

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Activity, CheckCircle2, XCircle, RotateCcw, Database } from 'lucide-react'

export const OverviewCards = ({ metrics }: { metrics: any }) => {
    const cards = [
        { title: 'Total Jobs', value: metrics?.total_jobs || 0, icon: RotateCcw, color: 'text-blue-600', bg: 'bg-blue-100' },
        { title: 'Running', value: metrics?.running_jobs || 0, icon: Activity, color: 'text-yellow-600', bg: 'bg-yellow-100' },
        { title: 'Completed', value: metrics?.completed_jobs || 0, icon: CheckCircle2, color: 'text-green-600', bg: 'bg-green-100' },
        { title: 'Failed', value: metrics?.failed_jobs || 0, icon: XCircle, color: 'text-red-600', bg: 'bg-red-100' },
    ]

    const totalCollected = metrics?.total_collected || 0
    const totalTarget = metrics?.total_target || 1

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {cards.map((card) => (
                <Card key={card.title} className="hover:shadow-md transition-shadow">
                    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                        <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">{card.title}</CardTitle>
                        <div className={`p-1.5 rounded-md ${card.bg}`}>
                            <card.icon className={`h-4 w-4 ${card.color}`} />
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{card.value}</div>
                    </CardContent>
                </Card>
            ))}
            <Card className="hover:shadow-md transition-shadow bg-gradient-to-br from-indigo-50 to-white">
                <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                    <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Collected</CardTitle>
                    <Database className="h-4 w-4 text-indigo-600" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{totalCollected.toLocaleString()}</div>
                    <p className="text-[10px] text-muted-foreground mt-1 tracking-tighter">
                        Overall efficiency: {Math.round((totalCollected / totalTarget) * 100)}%
                    </p>
                </CardContent>
            </Card>
        </div>
    )
}
