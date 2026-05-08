'use client'

import { useEffect, useState, memo, Suspense } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts'
import dynamic from 'next/dynamic'
import { AlertCircle, TrendingUp, Users, MapPin, Star } from 'lucide-react'
import apiClient from '@/services/apiClient'

// Dynamic import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false })

// Timeout utility
const fetchWithTimeout = async (endpoint, timeoutMs = 15000) => {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await apiClient.get(endpoint)
    return response.data
  } finally {
    clearTimeout(timeoutId)
  }
}

const COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']

// Chart Components with memo to prevent re-renders
const ChartCard = memo(({ title, description, children, loading }) => (
  <Card>
    <CardHeader>
      <CardTitle>{title}</CardTitle>
      <CardDescription>{description}</CardDescription>
    </CardHeader>
    <CardContent>
      {loading ? (
        <div className="flex items-center justify-center h-[300px] text-muted-foreground">
          <div className="text-center">
            <AlertCircle className="h-8 w-8 mx-auto mb-2" />
            <p>Đang tải dữ liệu...</p>
          </div>
        </div>
      ) : (
        children
      )}
    </CardContent>
  </Card>
))
ChartCard.displayName = 'ChartCard'

export default function SmartTravelDashboard() {
  const [overview, setOverview] = useState(null)
  const [placesByCategory, setPlacesByCategory] = useState(null)
  const [placesByRating, setPlacesByRating] = useState(null)
  const [topPlaces, setTopPlaces] = useState(null)
  const [placesByProvince, setPlacesByProvince] = useState(null)
  const [averageRating, setAverageRating] = useState(null)
  const [mapData, setMapData] = useState(null)
  const [cityRanking, setCityRanking] = useState(null)
  const [heatmapData, setHeatmapData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)

        // Parallel fetch with timeout - chia ra 3 groups để tối ưu
        // Group 1: Critical data (Overview, Categories, Rating)
        const group1 = Promise.all([
          fetchWithTimeout('/api/smart-travel/dashboard/overview').catch(() => null),
          fetchWithTimeout('/api/smart-travel/dashboard/places-by-category').catch(() => null),
          fetchWithTimeout('/api/smart-travel/dashboard/places-by-rating').catch(() => null),
          fetchWithTimeout('/api/smart-travel/dashboard/city-ranking').catch(() => null),
        ])

        // Group 2: Secondary data (Top places, Province, Average rating)
        const group2 = Promise.all([
          fetchWithTimeout('/api/smart-travel/dashboard/top-places').catch(() => null),
          fetchWithTimeout('/api/smart-travel/dashboard/places-by-province').catch(() => null),
          fetchWithTimeout('/api/smart-travel/dashboard/average-rating-by-category').catch(() => null),
          fetchWithTimeout('/api/smart-travel/dashboard/city-category-matrix', 30000).catch(() => null), // Increased timeout for heatmap
        ])

        // Group 3: Map data (Heavy, load last)
        const group3 = fetchWithTimeout('/api/smart-travel/dashboard/map-data', 20000).catch(() => null)

        // Wait for critical data first
        const [overviewRes, categoryRes, ratingRes, cityRes] = await group1
        setOverview(overviewRes)
        setPlacesByCategory(categoryRes)
        setPlacesByRating(ratingRes)
        setCityRanking(cityRes)

        // Then load secondary data
        const [topRes, provinceRes, ratingCategoryRes, heatmapRes] = await group2
        setTopPlaces(topRes)
        setPlacesByProvince(provinceRes)
        setAverageRating(ratingCategoryRes)
        setHeatmapData(heatmapRes)

        // Finally load map data
        const mapRes = await group3
        setMapData(mapRes)

        setLoading(false)
      } catch (err) {
        console.error('[Smart Travel Dashboard Error]', err)
        setError('Failed to load dashboard data: ' + (err.message || 'Unknown error'))
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-8">
        {/* Header Skeleton */}
        <div className="space-y-4">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-6 w-96" />
        </div>

        {/* Metrics Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[...Array(2)].map((_, i) => (
            <Skeleton key={`metric-${i}`} className="h-32" />
          ))}
        </div>

        {/* Charts Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(2)].map((_, i) => (
            <Skeleton key={`chart1-${i}`} className="h-96" />
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(2)].map((_, i) => (
            <Skeleton key={`chart2-${i}`} className="h-96" />
          ))}
        </div>

        {/* Table Skeleton */}
        <Skeleton className="h-80" />

        {/* Map Skeleton */}
        <Skeleton className="h-[600px]" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Key Metrics Cards */}
      {overview ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Total Places Card */}
          <Card className="group bg-gradient-to-br from-blue-50 to-blue-100/50 border-blue-200 hover:shadow-lg transition-all duration-200 overflow-hidden">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between mb-2">
                <CardTitle className="text-sm font-medium text-slate-700">Tổng số Places</CardTitle>
                <div className="p-2 bg-blue-100 rounded-lg">
                  <MapPin className="h-4 w-4 text-blue-600" />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl lg:text-4xl font-bold text-blue-900">{overview.totalPlaces?.toLocaleString()}</div>
              <p className="text-xs text-blue-700 mt-1">từ MongoDB Atlas</p>
            </CardContent>
          </Card>

          {/* Average Rating Card */}
          <Card className="group bg-gradient-to-br from-yellow-50 to-yellow-100/50 border-yellow-200 hover:shadow-lg transition-all duration-200 overflow-hidden">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between mb-2">
                <CardTitle className="text-sm font-medium text-slate-700">Rating Trung Bình</CardTitle>
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <Star className="h-4 w-4 text-yellow-600" />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl lg:text-4xl font-bold text-yellow-900">{overview.averageRating}</div>
              <p className="text-xs text-yellow-700 mt-1">Min: {overview.minRating} | Max: {overview.maxRating}</p>
            </CardContent>
          </Card>
        </div>
      ) : (
        loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
          </div>
        )
      )}

      {/* PRIORITY 1: City Ranking Table */}
      <Card className="border-2 border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50/30">
        <CardHeader className="bg-gradient-to-r from-amber-100 to-orange-100 border-b border-amber-200">
          <CardTitle className="text-amber-900 flex items-center gap-2">
            <span className="text-2xl">🏆</span>
            City Ranking Table (PRIORITY 1)
          </CardTitle>
          <CardDescription className="text-amber-700">Top 20 cities by average rating - Sorted by rating ⭐</CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          {cityRanking ? (
            <div className="overflow-x-auto rounded-lg border border-amber-100">
              <table className="w-full text-sm">
                <thead className="bg-gradient-to-r from-amber-600 to-orange-600 text-white sticky top-0">
                  <tr>
                    <th className="text-left py-3 px-4 font-semibold">Rank</th>
                    <th className="text-left py-3 px-4 font-semibold">City</th>
                    <th className="text-center py-3 px-4 font-semibold">Number of Places</th>
                    <th className="text-center py-3 px-4 font-semibold">Rating ⭐</th>
                    <th className="text-left py-3 px-4 font-semibold">Top Category</th>
                  </tr>
                </thead>
                <tbody>
                  {cityRanking.map?.((city, idx) => (
                    <tr key={idx} className="border-b border-amber-100 hover:bg-amber-50/50 transition">
                      <td className="py-3 px-4 font-bold text-lg">
                        {city.rank === 1 ? '🥇' : city.rank === 2 ? '🥈' : city.rank === 3 ? '🥉' : `#${city.rank}`}
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-800">{city.city}</td>
                      <td className="py-3 px-4 text-center font-medium text-slate-600">{city.count.toLocaleString()}</td>
                      <td className="py-3 px-4 text-center">
                        <Badge className={city.avgRating >= 4.5 ? 'bg-green-500 text-white hover:bg-green-600' : city.avgRating >= 4.3 ? 'bg-blue-500 text-white hover:bg-blue-600' : 'bg-yellow-500 text-white hover:bg-yellow-600'}>
                          {city.avgRating.toFixed(2)} ⭐
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-xs text-slate-600">{city.topCategory?.replace(/_/g, ' ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="flex items-center justify-center h-[200px] text-muted-foreground">
              <AlertCircle className="h-8 w-8 mx-auto" />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Places by Category - Bar Chart */}
        <Card className="border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-cyan-50/30">
          <CardHeader className="bg-gradient-to-r from-blue-100 to-cyan-100 border-b border-blue-200">
            <CardTitle className="text-blue-900 flex items-center gap-2">
              <span className="text-2xl">📊</span>
              Number of Places by Category
            </CardTitle>
            <CardDescription className="text-blue-700">Top 20 categories - Distribution by place type</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            {placesByCategory ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={placesByCategory.categories}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#bfdbfe" />
                  <XAxis dataKey="category" angle={-45} textAnchor="end" height={80} stroke="#1e40af" />
                  <YAxis stroke="#1e40af" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#eff6ff', border: '1px solid #3b82f6' }}
                    cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }}
                  />
                  <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                <div className="text-center">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                  <p>Đang tải dữ liệu...</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Places by Rating - Pie Chart */}
        <Card className="border-2 border-pink-200 bg-gradient-to-br from-pink-50 to-rose-50/30">
          <CardHeader className="bg-gradient-to-r from-pink-100 to-rose-100 border-b border-pink-200">
            <CardTitle className="text-pink-900 flex items-center gap-2">
              <span className="text-2xl">📈</span>
              Places Distribution by Rating
            </CardTitle>
            <CardDescription className="text-pink-700">Distribution by rating ranges - Distribution by rating ranges</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            {placesByRating ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={placesByRating.ratingDistribution}
                    dataKey="count"
                    nameKey="range"
                    cx="50%"
                    cy="50%"
                    label
                  >
                    {COLORS.map((color, index) => (
                      <Cell key={`cell-${index}`} fill={color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#fff7ed', border: '1px solid #fb7185' }} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                <div className="text-center">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                  <p>Đang tải dữ liệu...</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Average Rating by Category - Line Chart */}
        <Card className="border-2 border-teal-200 bg-gradient-to-br from-teal-50 to-cyan-50/30">
          <CardHeader className="bg-gradient-to-r from-teal-100 to-cyan-100 border-b border-teal-200">
            <CardTitle className="text-teal-900 flex items-center gap-2">
              <span className="text-2xl">📈</span>
              Average Rating by Category
            </CardTitle>
            <CardDescription className="text-teal-700">Top 20 categories by average rating - Ranking average</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            {averageRating ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={averageRating.categoryRatings}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ccfbf1" />
                  <XAxis dataKey="category" angle={-45} textAnchor="end" height={80} stroke="#0f766e" />
                  <YAxis domain={[0, 5]} stroke="#0f766e" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#f0fdfa', border: '1px solid #14b8a6' }}
                    cursor={{ stroke: 'rgba(20, 184, 166, 0.3)', strokeWidth: 2 }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="avgRating" 
                    stroke="#10b981" 
                    strokeWidth={2.5}
                    dot={{ fill: '#10b981', r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                <div className="text-center">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                  <p>Đang tải dữ liệu...</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Places by Province - Horizontal Bar Chart */}
        <Card className="border-2 border-violet-200 bg-gradient-to-br from-violet-50 to-purple-50/30">
          <CardHeader className="bg-gradient-to-r from-violet-100 to-purple-100 border-b border-violet-200">
            <CardTitle className="text-violet-900 flex items-center gap-2">
              <span className="text-2xl">🗺️</span>
              Number of Places by Province
            </CardTitle>
            <CardDescription className="text-violet-700">Top 20 provinces - Regional distribution</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            {placesByProvince ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={placesByProvince.provinces} layout="vertical" margin={{ top: 5, right: 30, left: 150, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e9d5ff" />
                  <XAxis type="number" stroke="#6d28d9" />
                  <YAxis dataKey="province" type="category" width={140} stroke="#6d28d9" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#faf5ff', border: '1px solid #8b5cf6' }}
                    cursor={{ fill: 'rgba(139, 92, 246, 0.1)' }}
                  />
                  <Bar dataKey="count" fill="#8b5cf6" radius={[0, 8, 8, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                <div className="text-center">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                  <p>Đang tải dữ liệu...</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 
        PRIORITY 2: Heatmap - Cities vs Categories (MOST VALUABLE!)
        This heatmap shows the relationship between cities and place categories.
        "Where to find what?" - Helps users understand which types of places are most common in each city.
        For example: Which city has the most restaurants? Which city has the best shopping?
        Data source: MongoDB aggregation counting places by city and category combinations.
      */}
      <Card className="border-2 border-orange-200 bg-gradient-to-br from-orange-50 to-amber-50/30">
        <CardHeader className="bg-gradient-to-r from-orange-100 to-amber-100 border-b border-orange-200">
          <CardTitle className="text-orange-900 flex items-center gap-2">
            <span className="text-2xl">🔥</span>
            Heatmap - Cities vs Categories (PRIORITY 2)
          </CardTitle>
          <CardDescription className="text-orange-700">"Where to find what?" - Relationship between cities and place categories 🎯</CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          {heatmapData ? (
            <div className="space-y-4">
              <div className="text-sm text-orange-700 bg-orange-50 p-3 rounded-lg border border-orange-100">
                💡 Each cell shows the number of places: Dark color = many places, Light color = few places
              </div>
              <div className="overflow-x-auto rounded-lg border border-orange-100">
                <table className="text-xs border-collapse w-full">
                  <thead>
                    <tr className="bg-gradient-to-r from-orange-600 to-amber-600">
                      <th className="p-2 text-left text-white font-semibold min-w-24 sticky left-0 z-10">City</th>
                      {heatmapData.categories?.slice(0, 12).map((cat) => (
                        <th 
                          key={cat} 
                          className="p-2 text-center text-white font-semibold min-w-12"
                          title={cat}
                        >
                          <div className="text-xs">{cat?.slice(0, 6)}</div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {heatmapData.cities?.slice(0, 12).map((city, cityIdx) => (
                      <tr key={city} className="border-b border-orange-100 hover:bg-orange-50/30 transition">
                        <td className="p-2 font-bold text-orange-900 bg-orange-50 sticky left-0 z-10 min-w-24 border-r border-orange-200">{city}</td>
                        {heatmapData.matrix?.[cityIdx]?.slice(0, 12).map((value, catIdx) => {
                          const percentage = (value / (heatmapData.maxValue || 1)) * 100;
                          let bgColor = 'bg-white';
                          let textColor = 'text-slate-700';
                          
                          if (percentage > 75) {
                            bgColor = 'bg-red-600';
                            textColor = 'text-white';
                          } else if (percentage > 50) {
                            bgColor = 'bg-red-400';
                            textColor = 'text-white';
                          } else if (percentage > 25) {
                            bgColor = 'bg-orange-300';
                            textColor = 'text-white';
                          } else if (percentage > 10) {
                            bgColor = 'bg-orange-100';
                            textColor = 'text-orange-900';
                          } else if (value > 0) {
                            bgColor = 'bg-gray-50';
                            textColor = 'text-gray-600';
                          }
                          
                          return (
                            <td 
                              key={`${city}-${catIdx}`}
                              className={`p-2 text-center font-bold ${bgColor} ${textColor} border border-orange-100 hover:opacity-90 cursor-pointer transition min-w-12`}
                              title={`${city} + ${heatmapData.categories?.[catIdx]}: ${value} places (${percentage.toFixed(0)}%)`}
                            >
                              {value > 0 ? value : '–'}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* Legend */}
              <div className="flex flex-wrap items-center gap-4 text-xs p-3 bg-orange-50 rounded-lg border border-orange-100">
                <span className="font-bold text-orange-900">Legend:</span>
                <div className="flex items-center gap-2">
                  <div className="w-5 h-4 bg-red-600 rounded" />
                  <span className="text-orange-900">75-100% (Very High)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-5 h-4 bg-red-400 rounded" />
                  <span className="text-orange-900">50-75% (High)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-5 h-4 bg-orange-300 rounded" />
                  <span className="text-orange-900">25-50% (Medium)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-5 h-4 bg-orange-100 rounded border border-orange-300" />
                  <span className="text-orange-900">10-25% (Low)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-5 h-4 bg-gray-50 rounded border border-gray-300" />
                  <span className="text-orange-900">1-10% (Very Low)</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-muted-foreground">
              <div className="text-center">
                <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                <p>Đang tải dữ liệu heatmap...</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Top 10 Highest Rated Places */}
      <Card className="border-2 border-green-200 bg-gradient-to-br from-green-50 to-emerald-50/30">
        <CardHeader className="bg-gradient-to-r from-green-100 to-emerald-100 border-b border-green-200">
          <CardTitle className="text-green-900 flex items-center gap-2">
            <span className="text-2xl">⭐</span>
            Top 10 Highest Rated Places (PRIORITY 3)
          </CardTitle>
          <CardDescription className="text-green-700">Best rated places on the platform - Highest rated places overall</CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          {topPlaces ? (
            <div className="overflow-x-auto rounded-lg border border-green-100">
              <table className="w-full text-sm">
                <thead className="bg-gradient-to-r from-green-600 to-emerald-600 text-white sticky top-0">
                  <tr>
                    <th className="text-left py-3 px-4 font-semibold">Rank</th>
                    <th className="text-left py-3 px-4 font-semibold">Tên Place</th>
                    <th className="text-left py-3 px-4 font-semibold">Category</th>
                    <th className="text-center py-3 px-4 font-semibold">Rating</th>
                    <th className="text-center py-3 px-4 font-semibold">Review Count</th>
                  </tr>
                </thead>
                <tbody>
                  {topPlaces.topPlaces?.map((place, idx) => (
                    <tr key={place.id} className="border-b border-green-100 hover:bg-green-50/50 transition">
                      <td className="py-3 px-4 font-bold text-lg text-green-700">#{idx + 1}</td>
                      <td className="py-3 px-4 font-semibold text-slate-800">{place.name}</td>
                      <td className="py-3 px-4">
                        <Badge className="bg-green-100 text-green-800 hover:bg-green-200">{place.category?.replace(/_/g, ' ')}</Badge>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <Badge className="bg-yellow-500 text-white hover:bg-yellow-600 font-semibold">
                          {place.rating?.toFixed(2)} ⭐
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-center font-medium text-slate-600">{place.reviewCount?.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="flex items-center justify-center h-[200px] text-muted-foreground">
              <AlertCircle className="h-8 w-8 mx-auto" />
            </div>
          )}
        </CardContent>
      </Card>

      {/* 
        Map Scatter Chart - Geographic Distribution
        Shows the geographical distribution of travel places worldwide.
        Uses Plotly.js with Mapbox for interactive mapping.
        Each point represents a place with color coding based on rating.
        Data source: MongoDB places collection with latitude/longitude coordinates.
        Performance: Heavy data load (500+ points), loaded last in the sequence.
      */}
      {/* Map Scatter Chart - Lazy Load
      <Card>
        <CardHeader>
          <CardTitle>Map - Distribution of Tourist Places</CardTitle>
          <CardDescription>Geographic location of {mapData?.totalPoints || 0} places on the world map</CardDescription>
        </CardHeader>
        <CardContent>
          {mapData ? (
            <div className="w-full h-[600px]">
              <Plot
                data={[{
                  type: 'scattermapbox',
                  lat: mapData.mapData?.map(point => point.lat) || [],
                  lon: mapData.mapData?.map(point => point.lon) || [],
                  mode: 'markers',
                  marker: {
                    size: 5,
                    color: mapData.mapData?.map(point => point.rating) || [],
                    colorscale: 'Viridis',
                    showscale: true,
                    colorbar: {
                      title: 'Rating',
                      titleside: 'right'
                    },
                    opacity: 0.7
                  },
                  text: mapData.mapData?.map(point => 
                    `<b>${point.name}</b><br>` +
                    `Category: ${point.category}<br>` +
                    `Rating: ${point.rating} ⭐<br>` +
                    `Reviews: ${point.reviewCount}`
                  ) || [],
                  hoverinfo: 'text'
                }]}
                layout={{
                  mapbox: {
                    style: 'open-street-map',
                    center: { lat: 20, lon: 0 },
                    zoom: 1
                  },
                  margin: { r: 0, t: 0, l: 0, b: 0 },
                  height: 600,
                  showlegend: false,
                  paper_bgcolor: 'rgba(0,0,0,0)',
                  plot_bgcolor: 'rgba(0,0,0,0)'
                }}
                config={{
                  mapboxAccessToken: process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN || '',
                  displayModeBar: true,
                  displaylogo: false,
                  modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d', 'autoScale2d'],
                  responsive: true
                }}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
              />
            </div>
          ) : (
            <div className="flex items-center justify-center h-[600px] text-muted-foreground">
              <div className="text-center">
                <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                <p>Loading map data...</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card> */}

      {/* Data Info */}
      <Card className="bg-muted/50">
        <CardHeader>
          <CardTitle className="text-sm">ℹ️ Data Information</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>✅ Data source: <code className="bg-black/10 px-2 py-1 rounded">smart_travel.places</code> (MongoDB Atlas)</p>
          <p>✅ Queries written using MongoDB Aggregation Pipeline</p>
          <p>✅ Charts rendered using Recharts library (no external tools)</p>
          <p>✅ Last updated: {overview?.timestamp}</p>
        </CardContent>
      </Card>
    </div>
  )
}
