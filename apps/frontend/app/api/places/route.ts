import { NextRequest, NextResponse } from 'next/server'
import axios from 'axios'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const city = searchParams.get('city')
    const category = searchParams.get('category')

    const response = await axios.get('http://backend:8000/api/places', {
      params: { city, category }
    })

    return NextResponse.json(response.data)
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch places' }, { status: 500 })
  }
}