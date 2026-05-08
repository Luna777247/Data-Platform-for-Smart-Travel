// frontendphp/components/pipeline-monitor/progress-bar.tsx
'use client'

import { Progress } from '@/components/ui/progress'

interface ProgressBarProps {
    current: int;
    target: int;
    status: string;
}

export const ProgressBar = ({ current, target, status }: ProgressBarProps) => {
    const percentage = Math.min(Math.round((current / target) * 100), 100)

    const getProgressColor = () => {
        if (status === 'failed') return 'bg-red-500'
        if (percentage === 100) return 'bg-green-500'
        return 'bg-blue-500'
    }

    return (
        <div className="w-full space-y-1">
            <div className="flex justify-between text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                <span>{percentage}%</span>
                <span>{current} / {target}</span>
            </div>
            <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden border border-slate-200">
                <div
                    className={`h-full transition-all duration-500 ease-out ${getProgressColor()} ${status === 'running' ? 'animate-shimmer bg-gradient-to-r from-transparent via-white/30 to-transparent' : ''}`}
                    style={{ width: `${percentage}%`, backgroundSize: '200% 100%' }}
                />
            </div>
        </div>
    )
}
