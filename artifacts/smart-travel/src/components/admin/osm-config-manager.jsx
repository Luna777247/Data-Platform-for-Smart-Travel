
import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Map, Plus, Trash2, Save, RefreshCcw, Globe, Server, Info } from 'lucide-react'
import apiClient from '../../services/apiClient.js'
import { toast } from 'sonner'

export function AdminOsmConfigManager() {
    const [config, setConfig] = useState({ cities: {}, overpass_urls: [] })
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [newCityKey, setNewCityKey] = useState('')
    const [newCityName, setNewCityName] = useState('')

    const fetchConfig = async () => {
        try {
            setLoading(true)
            const response = await apiClient.get('/api/osm/config')
            setConfig(response.data || { cities: {}, overpass_urls: [] })
        } catch (error) {
            console.error('Error fetching OSM config:', error)
            toast.error('Failed to load OSM configuration')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchConfig()
    }, [])

    const handleSave = async () => {
        try {
            setSaving(true)
            const response = await apiClient.put('/api/osm/config', config)
            if (response.data.status === 'success') {
                toast.success('OSM configuration saved')
            } else {
                toast.error(response.data.message || 'Failed to save configuration')
            }
        } catch (error) {
            toast.error('Error saving configuration')
        } finally {
            setSaving(false)
        }
    }

    const handleAddCity = () => {
        if (!newCityKey.trim() || !newCityName.trim()) {
            toast.error('City ID and Name are required')
            return
        }

        const key = newCityKey.trim().toLowerCase()
        if (config.cities[key]) {
            toast.error('City ID already exists')
            return
        }

        const updatedCities = {
            ...config.cities,
            [key]: { name: newCityName.trim(), bbox: '' }
        }

        setConfig({ ...config, cities: updatedCities })
        setNewCityKey('')
        setNewCityName('')
    }

    const handleRemoveCity = (key) => {
        const updatedCities = { ...config.cities }
        delete updatedCities[key]
        setConfig({ ...config, cities: updatedCities })
    }

    const handleUpdateCity = (key, field, value) => {
        setConfig({
            ...config,
            cities: {
                ...config.cities,
                [key]: { ...config.cities[key], [field]: value }
            }
        })
    }

    const handleUpdateUrls = (value) => {
        // Assuming comma separated or line separated
        const urls = value.split('\n').map(u => u.trim()).filter(u => u.length > 0)
        setConfig({ ...config, overpass_urls: urls })
    }

    return (
        <div className="space-y-6 pb-20">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold flex items-center gap-2">
                    <Globe className="w-6 h-6 text-emerald-600" />
                    OSM Ingestion Config
                </h2>
                <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={fetchConfig} disabled={loading}>
                        <RefreshCcw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                    <Button size="sm" onClick={handleSave} disabled={saving || loading} className="bg-emerald-600 hover:bg-emerald-700">
                        <Save className="w-4 h-4 mr-2" />
                        {saving ? 'Saving...' : 'Save All Changes'}
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    <Card>
                        <CardHeader className="bg-slate-50/50">
                            <CardTitle className="text-lg flex items-center gap-2">
                                <Map className="w-5 h-5 text-emerald-500" />
                                Target Cities & Regions
                            </CardTitle>
                            <CardDescription>
                                Configure the areas where data will be harvested from OpenStreetMap.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="pt-6">
                            <div className="flex flex-wrap gap-4 mb-6 p-4 bg-emerald-50/50 rounded-lg border border-emerald-100">
                                <div className="flex-1 min-w-[150px]">
                                    <Label className="text-xs uppercase text-emerald-700 font-bold">City ID (key)</Label>
                                    <Input
                                        placeholder="e.g. hanoi"
                                        value={newCityKey}
                                        onChange={(e) => setNewCityKey(e.target.value)}
                                        className="mt-1"
                                    />
                                </div>
                                <div className="flex-[2] min-w-[200px]">
                                    <Label className="text-xs uppercase text-emerald-700 font-bold">Display Name (OSM Area Name)</Label>
                                    <Input
                                        placeholder="e.g. Thành phố Hà Nội"
                                        value={newCityName}
                                        onChange={(e) => setNewCityName(e.target.value)}
                                        className="mt-1"
                                    />
                                </div>
                                <div className="flex items-end">
                                    <Button onClick={handleAddCity}>
                                        <Plus className="w-4 h-4 mr-2" />
                                        Add City
                                    </Button>
                                </div>
                            </div>

                            <div className="border rounded-md">
                                <Table>
                                    <TableHeader>
                                        <TableRow className="bg-slate-50">
                                            <TableHead className="w-32">ID</TableHead>
                                            <TableHead>OSM Area Name</TableHead>
                                            <TableHead className="w-1/3">Bounding Box (Optional)</TableHead>
                                            <TableHead className="w-20"></TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {Object.entries(config.cities).map(([key, city]) => (
                                            <TableRow key={key}>
                                                <TableCell className="font-mono text-xs">{key}</TableCell>
                                                <TableCell>
                                                    <Input
                                                        value={city.name}
                                                        onChange={(e) => handleUpdateCity(key, 'name', e.target.value)}
                                                        className="h-8 text-sm"
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    <Input
                                                        value={city.bbox || ''}
                                                        placeholder="S,W,N,E (e.g. 20.7,105.7,21.3,106.0)"
                                                        onChange={(e) => handleUpdateCity(key, 'bbox', e.target.value)}
                                                        className="h-8 text-xs font-mono"
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleRemoveCity(key)}
                                                        className="text-red-500 hover:text-red-700 hover:bg-red-50"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                        {Object.keys(config.cities).length === 0 && (
                                            <TableRow>
                                                <TableCell colSpan={4} className="text-center py-10 text-muted-foreground italic">
                                                    No cities configured.
                                                </TableCell>
                                            </TableRow>
                                        )}
                                    </TableBody>
                                </Table>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                <div className="space-y-6">
                    <Card>
                        <CardHeader className="bg-slate-50/50">
                            <CardTitle className="text-lg flex items-center gap-2">
                                <Server className="w-5 h-5 text-emerald-500" />
                                Overpass API Cluster
                            </CardTitle>
                            <CardDescription>
                                List of Overpass API endpoints (rotated to avoid limits).
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="pt-4 space-y-4">
                            <div className="space-y-2">
                                <Label className="text-xs font-bold uppercase text-slate-500">Endpoints (One per line)</Label>
                                <textarea
                                    className="w-full min-h-[200px] p-3 text-xs font-mono border rounded-md focus:ring-2 focus:ring-emerald-500 outline-none"
                                    value={config.overpass_urls.join('\n')}
                                    onChange={(e) => handleUpdateUrls(e.target.value)}
                                />
                            </div>

                            <div className="bg-amber-50 p-3 rounded-lg border border-amber-100 flex gap-3">
                                <Info className="w-4 h-4 text-amber-600 flex-shrink-0 mt-1" />
                                <p className="text-[10px] text-amber-800 leading-relaxed">
                                    <strong>Advice:</strong> Use multiple public mirrors to increase throughput.
                                    The collector automatically switches to the next URL if rate limited (429).
                                </p>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="bg-emerald-50 border-emerald-200">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-bold text-emerald-800">Pro-Tip: Bounding Box</CardTitle>
                        </CardHeader>
                        <CardContent className="text-[11px] text-emerald-700 space-y-2">
                            <p>
                                If <strong>Bounding Box</strong> is empty, system uses <code>area["name"]="City Name"]</code>.
                                This is more accurate for administrative boundaries.
                            </p>
                            <p>
                                Use BBox for custom rectangular regions. Format: <code>south, west, north, east</code>.
                            </p>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}
