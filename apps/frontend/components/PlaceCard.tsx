import React from 'react'

interface Place {
  id: string
  name: string
  city: string
  category: string
  rating: number
  latitude: number
  longitude: number
}

interface PlaceCardProps {
  place: Place
}

export default function PlaceCard({ place }: PlaceCardProps) {
  return (
    <div className="border rounded-lg p-4 shadow-sm">
      <h3 className="font-semibold text-lg">{place.name}</h3>
      <p className="text-gray-600">{place.city} - {place.category}</p>
      <div className="flex items-center mt-2">
        <span className="text-yellow-500">★</span>
        <span className="ml-1">{place.rating}</span>
      </div>
      <p className="text-sm text-gray-500 mt-2">
        Lat: {place.latitude}, Lng: {place.longitude}
      </p>
    </div>
  )
}