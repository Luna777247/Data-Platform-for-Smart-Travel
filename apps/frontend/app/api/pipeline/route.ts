import { NextRequest, NextResponse } from 'next/server'
import axios from 'axios'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const response = await axios.post('http://backend:8000/api/pipeline/run', body)
    return NextResponse.json(response.data)
  } catch {
    return NextResponse.json({ error: 'Failed to run pipeline' }, { status: 500 })
  }
}

export async function GET() {
  try {
    const response = await axios.get('http://backend:8000/api/pipeline/runs')
    return NextResponse.json(response.data)
  } catch {
    return NextResponse.json({ error: 'Failed to fetch pipeline runs' }, { status: 500 })
  }
}