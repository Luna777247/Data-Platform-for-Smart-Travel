
import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { Sparkles, Save, RefreshCcw, Languages, ListFilter, Zap, ShieldCheck, AlertCircle } from 'lucide-react'
import apiClient from '../../services/apiClient.js'
import { toast } from 'sonner'

export function AdminEnrichmentConfigManager() {
    const [settings, setSettings] = useState({
        fields: '',
        language: 'vi',
        smart_delay: 2.0,
        daily_limit: 500
    })
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)

    const fetchSettings = async () => {
        try {
            setLoading(true)
            const response = await apiClient.get('/api/enrichment/config')
            setSettings(response.data || {
                fields: 'name,rating',
                language: 'vi',
                smart_delay: 2.0,
                daily_limit: 500
            })
        } catch (error) {
            console.error('Error fetching enrichment settings:', error)
            toast.error('Failed to load enrichment settings')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchSettings()
    }, [])

    const handleSave = async () => {
        try {
            setSaving(true)
            await apiClient.put('/api/enrichment/config', settings)
            toast.success('Enrichment settings updated')
        } catch (error) {
            toast.error('Failed to update settings')
        } finally {
            setSaving(false)
        }
    }

    if (loading) {
        return <div className="text-center py-10 text-muted-foreground italic">Loading settings...</div>
    }

    return (
        <div className="space-y-6 max-w-4xl">
            <div className="flex justify-between items-center px-1">
                <div>
                    <h2 className="text-2xl font-bold flex items-center gap-2">
                        <Sparkles className="w-6 h-6 text-amber-500" />
                        Enrichment Strategy
                    </h2>
                    <p className="text-sm text-muted-foreground">Configure how Google Maps data is enriched and harvested.</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={fetchSettings} disabled={loading}>
                        <RefreshCcw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                    <Button size="sm" onClick={handleSave} disabled={saving} className="bg-amber-600 hover:bg-amber-700">
                        <Save className="w-4 h-4 mr-2" />
                        {saving ? 'Saving...' : 'Save Strategy'}
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Data Fields */}
                <Card className="md:col-span-2">
                    <CardHeader className="bg-amber-50/50 pb-4">
                        <CardTitle className="text-lg flex items-center gap-2">
                            <ListFilter className="w-5 h-5 text-amber-600" />
                            Place Details Fields
                        </CardTitle>
                        <CardDescription>
                            Comma-separated list of fields to fetch from Google Place Details API.
                            Note: Some fields may incur higher costs or requirements.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="pt-6">
                        <div className="space-y-2">
                            <Label className="text-xs font-bold text-slate-500 uppercase">Selected Fields</Label>
                            <textarea
                                className="w-full min-h-[100px] p-3 text-sm font-mono border rounded-md focus:ring-2 focus:ring-amber-500 outline-none"
                                value={settings.fields}
                                onChange={(e) => setSettings({ ...settings, fields: e.target.value })}
                                placeholder="name,rating,reviews,..."
                            />
                            <div className="flex flex-wrap gap-2 pt-2">
                                <span className="text-[10px] bg-amber-100 text-amber-800 px-2 py-0.5 rounded">BASIC: name, geometry, icon, photos</span>
                                <span className="text-[10px] bg-amber-100 text-amber-800 px-2 py-0.5 rounded">CONTACT: formatted_phone_number, opening_hours, website</span>
                                <span className="text-[10px] bg-amber-100 text-amber-800 px-2 py-0.5 rounded">ATMOSPHERE: rating, reviews, user_ratings_total, price_level</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Language & Localozation */}
                <Card>
                    <CardHeader className="pb-4">
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Languages className="w-5 h-5 text-amber-600" />
                            Localization
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label>Response Language</Label>
                            <Select
                                value={settings.language}
                                onValueChange={(val) => setSettings({ ...settings, language: val })}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select language" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="vi">Vietnamese (vi)</SelectItem>
                                    <SelectItem value="en">English (en)</SelectItem>
                                    <SelectItem value="ja">Japanese (ja)</SelectItem>
                                    <SelectItem value="ko">Korean (ko)</SelectItem>
                                    <SelectItem value="fr">French (fr)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </CardContent>
                </Card>

                {/* Performance & Safety */}
                <Card>
                    <CardHeader className="pb-4">
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Zap className="w-5 h-5 text-amber-600" />
                            Safety & Performance
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <Label>Smart Delay (seconds)</Label>
                                <span className="text-sm font-bold text-amber-600">{settings.smart_delay}s</span>
                            </div>
                            <Slider
                                value={[settings.smart_delay]}
                                min={0.5}
                                max={10.0}
                                step={0.5}
                                onValueChange={(val) => setSettings({ ...settings, smart_delay: val[0] })}
                            />
                            <p className="text-[10px] text-muted-foreground italic">Higher delay reduces 429 errors but slows ingestion.</p>
                        </div>

                        <div className="space-y-2 border-t pt-4">
                            <div className="flex justify-between items-center">
                                <Label>Daily Limit (per Key)</Label>
                                <Input
                                    type="number"
                                    value={settings.daily_limit}
                                    onChange={(e) => setSettings({ ...settings, daily_limit: parseInt(e.target.value) })}
                                    className="w-24 text-right h-8"
                                />
                            </div>
                            <p className="text-[10px] text-muted-foreground italic">Free tier limit is usually 500 requests/day.</p>
                        </div>
                    </CardContent>
                </Card>

                {/* Summary Info */}
                <Card className="md:col-span-2 bg-slate-900 text-slate-100 border-none">
                    <CardContent className="pt-6">
                        <div className="flex items-start gap-4">
                            <div className="p-3 bg-amber-500/20 rounded-full">
                                <ShieldCheck className="w-6 h-6 text-amber-500" />
                            </div>
                            <div>
                                <h4 className="font-bold text-amber-500">Auto-Optimization Active</h4>
                                <p className="text-xs text-slate-400 leading-relaxed mt-1">
                                    The enrichment engine uses these settings to balance data quality and API costs.
                                    If the <code>SmartKeyManager</code> detects consistent 429 errors, it will override the delay
                                    temporarily to protect your API keys.
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="bg-red-50 border border-red-100 rounded-lg p-4 flex gap-3 text-red-800">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <div className="text-xs">
                    <strong>Warning:</strong> Changing field requirements may affect data warehouse schemas.
                    Make sure your serving layer can handle the new fields if you add custom attributes.
                </div>
            </div>
        </div>
    )
}
