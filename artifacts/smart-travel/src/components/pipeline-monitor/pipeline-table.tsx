// frontendphp/components/pipeline-monitor/pipeline-table.tsx

import { useState } from 'react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { StatusBadge } from './status-badge'
import { ProgressBar } from './progress-bar'
import { ArrowUpDown, Search } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

export const PipelineTable = ({ data }: { data: any[] }) => {
    const [filter, setFilter] = useState('')
    const [sortKey, setSortKey] = useState('city')
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')

    const filteredData = (data || [])
        .filter(item =>
            item.city.toLowerCase().includes(filter.toLowerCase()) ||
            item.type.toLowerCase().includes(filter.toLowerCase())
        )
        .sort((a, b) => {
            const direction = sortOrder === 'asc' ? 1 : -1
            if (typeof a[sortKey] === 'string') {
                return a[sortKey].localeCompare(b[sortKey]) * direction
            }
            return (a[sortKey] - b[sortKey]) * direction
        })

    const toggleSort = (key: string) => {
        if (sortKey === key) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
        } else {
            setSortKey(key)
            setSortOrder('asc')
        }
    }

    const formatDuration = (start: string, end: string) => {
        if (!start) return '--'
        const s = new Date(start).getTime()
        const e = end ? new Date(end).getTime() : new Date().getTime()
        const diff = Math.floor((e - s) / 1000)

        const m = Math.floor(diff / 60)
        const sec = diff % 60
        return `${m}m ${sec}s`
    }

    return (
        <div className="space-y-4">
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                    placeholder="Filter by city or type..."
                    className="pl-10 max-w-sm"
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                />
            </div>

            <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
                <Table>
                    <TableHeader className="bg-slate-50/50">
                        <TableRow>
                            <TableHead onClick={() => toggleSort('city')} className="cursor-pointer hover:text-blue-600 transition-colors">
                                City <ArrowUpDown className="inline h-3 w-3 ml-1" />
                            </TableHead>
                            <TableHead onClick={() => toggleSort('type')} className="cursor-pointer hover:text-blue-600 transition-colors">
                                Type <ArrowUpDown className="inline h-3 w-3 ml-1" />
                            </TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead className="w-[200px]">Progress</TableHead>
                            <TableHead className="text-right">Collected</TableHead>
                            <TableHead className="text-right">Target</TableHead>
                            <TableHead className="text-right">Duration</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {filteredData.length > 0 ? (
                            filteredData.map((job) => (
                                <TableRow
                                    key={`${job.city}-${job.type}`}
                                    className={job.status === 'running' ? 'bg-blue-50/30 font-medium' : ''}
                                >
                                    <td className="py-4 px-4 capitalize">{job.city}</td>
                                    <td className="py-4 px-4 capitalize text-slate-500">{job.type}</td>
                                    <td className="py-4 px-4"><StatusBadge status={job.status} /></td>
                                    <td className="py-4 px-4">
                                        <ProgressBar current={job.collected} target={job.target} status={job.status} />
                                    </td>
                                    <td className="py-4 px-4 text-right font-mono text-xs">{job.collected}</td>
                                    <td className="py-4 px-4 text-right font-mono text-xs">{job.target}</td>
                                    <td className="py-4 px-4 text-right text-xs text-muted-foreground">
                                        {formatDuration(job.start_time, job.end_time)}
                                    </td>
                                </TableRow>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={7} className="h-64 text-center text-muted-foreground">
                                    No active pipelines found for the filter.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    )
}
