// frontendphp/components/pipeline-monitor/status-badge.tsx
'use client'

import { Badge } from '@/components/ui/badge'

export const StatusBadge = ({ status }: { status: string }) => {
    const configs: Record<string, { label: string, className: string }> = {
        running: { label: 'Running', className: 'bg-yellow-500 hover:bg-yellow-600 text-white animate-pulse' },
        done: { label: 'Done', className: 'bg-green-500 hover:bg-green-600 text-white' },
        failed: { label: 'Failed', className: 'bg-red-500 hover:bg-red-600 text-white' },
        pending: { label: 'Pending', className: 'bg-gray-400 hover:bg-gray-500 text-white' }
    }

    const { label, className } = configs[status.toLowerCase()] || configs.pending

    return (
        <Badge className={`${className} px-2 py-1 text-xs font-semibold rounded-full border-none`}>
            {label}
        </Badge>
    )
}
