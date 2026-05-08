
import { useState, useEffect } from 'react'
import axios from 'axios'

interface Place {
  id: string
  name: string
  city: string
  category: string
  rating: number
  latitude: number
  longitude: number
}

export default function Dashboard() {
  const [places, setPlaces] = useState<Place[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPlaces()
  }, [])

  const fetchPlaces = async () => {
    try {
      const response = await axios.get('/api/places')
      setPlaces(response.data)
    } catch (err) {
      setError('Failed to fetch places')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div>Loading...</div>
  if (error) return <div>Error: {error}</div>

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Smart Travel Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {places.map((place) => (
          <div key={place.id} className="border rounded-lg p-4">
            <h2 className="font-semibold">{place.name}</h2>
            <p>{place.city} - {place.category}</p>
            <p>Rating: {place.rating}</p>
          </div>
        ))}
      </div>
    </div>
  )
}