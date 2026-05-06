'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Key, Plus, Trash2, RefreshCcw, ShieldCheck, AlertTriangle, ShieldAlert } from 'lucide-react'
import apiClient from '../../services/apiClient.js'
import { toast } from 'sonner'

export function AdminApiKeyManager() {
    const [keys, setKeys] = useState([])
    const [newKey, setNewKey] = useState('')
    const [loading, setLoading] = useState(true)
    const [submitting, setSubmitting] = useState(false)

    const fetchKeys = async () => {
        try {
            setLoading(true)
            const response = await apiClient.get('/api/keys/rapidapi')
            setKeys(response.data || [])
        } catch (error) {
            console.error('Error fetching API keys:', error)
            toast.error('Failed to load API keys')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchKeys()
    }, [])

    const handleAddKey = async () => {
        if (!newKey.trim()) return

        try {
            setSubmitting(true)
            const response = await apiClient.post('/api/keys/rapidapi', { key: newKey.trim() })
            if (response.data.status === 'success') {
                toast.success('API Key added successfully')
                setNewKey('')
                fetchKeys()
            } else {
                toast.error(response.data.message || 'Failed to add key')
            }
        } catch (error) {
            toast.error('Error adding API key')
        } finally {
            setSubmitting(false)
        }
    }

    const handleDeleteKey = async (id) => {
        if (!confirm('Are you sure you want to delete this key?')) return

        try {
            const response = await apiClient.delete(`/api/keys/rapidapi/${id}`)
            if (response.data.status === 'success') {
                toast.success('API Key deleted')
                fetchKeys()
            } else {
                toast.error(response.data.message || 'Failed to delete key')
            }
        } catch (error) {
            toast.error('Error deleting API key')
        }
    }

    const getStatusBadge = (status, code) => {
        if (code === 200) {
            return <Badge className="bg-green-100 text-green-800 hover:bg-green-100 border-green-200">
                <ShieldCheck className="w-3 h-3 mr-1" /> Ready
            </Badge>
        }
        if (code === 403) {
            return <Badge variant="destructive" className="bg-red-100 text-red-800 hover:bg-red-100 border-red-200">
                <ShieldAlert className="w-3 h-3 mr-1" /> Blocked (403)
            </Badge>
        }
        if (code === 429) {
            return <Badge variant="warning" className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100 border-yellow-200">
                <AlertTriangle className="w-3 h-3 mr-1" /> Rate Limit (429)
            </Badge>
        }
        return <Badge variant="secondary">{status}</Badge>
    }

    return (
        <div className="space-y-6">
            <Card className="border-2 border-blue-100 shadow-sm">
                <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle className="text-xl flex items-center gap-2">
                                <Key className="w-5 h-5 text-blue-600" />
                                RapidAPI Key Manager
                            </CardTitle>
                            <CardDescription>
                                Manage your Google Places API key pool (Total: {keys.length} keys)
                            </CardDescription>
                        </div>
                        <Button variant="outline" size="sm" onClick={fetchKeys} disabled={loading} className="bg-white">
                            <RefreshCcw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                            Refresh
                        </Button>
                    </div>
                </CardHeader>
                <CardContent className="pt-6">
                    <div className="flex gap-4 mb-8">
                        <div className="relative flex-1">
                            <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                            <Input
                                placeholder="Enter new RapidAPI Key..."
                                value={newKey}
                                onChange={(e) => setNewKey(e.target.value)}
                                className="pl-10"
                            />
                        </div>
                        <Button onClick={handleAddKey} disabled={submitting || !newKey}>
                            <Plus className="w-4 h-4 mr-2" />
                            Add Key
                        </Button>
                    </div>

                    <div className="rounded-md border border-slate-200 overflow-hidden">
                        <Table>
                            <TableHeader>
                                <TableRow className="bg-slate-50">
                                    <TableHead className="w-16">ID</TableHead>
                                    <TableHead>Key Fragment</TableHead>
                                    <TableHead>Label</TableHead>
                                    <TableHead>Current Status</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {loading && keys.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="text-center py-10 text-muted-foreground italic">
                                            Loading keys...
                                        </TableCell>
                                    </TableRow>
                                ) : keys.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="text-center py-10 text-muted-foreground italic">
                                            No keys found. Add one above.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    keys.map((item) => (
                                        <TableRow key={item.id} className="hover:bg-slate-50/50">
                                            <TableCell className="font-mono text-xs text-slate-500">#{item.id}</TableCell>
                                            <TableCell className="font-mono text-sm font-medium">{item.short_key}</TableCell>
                                            <TableCell>
                                                <span className="text-xs font-semibold px-2 py-1 bg-slate-100 rounded text-slate-600">
                                                    {item.label}
                                                </span>
                                            </TableCell>
                                            <TableCell>{getStatusBadge(item.status, item.status_code)}</TableCell>
                                            <TableCell className="text-right">
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => handleDeleteKey(item.id)}
                                                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </CardContent>
            </Card>

            <Card className="bg-amber-50 border-amber-200">
                <CardContent className="pt-4 text-xs text-amber-800 flex gap-2">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                    <p>
                        <strong>Note:</strong> Keys are used in rotation to avoid reaching the free tier limit (500 requests/day per key).
                        Blocked keys are automatically cooled down by the <code>SmartKeyManager</code> in the backend.
                        Changes here take effect immediately for new pipeline runs.
                    </p>
                </CardContent>
            </Card>
        </div>
    )
}
