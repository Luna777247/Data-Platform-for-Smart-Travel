import axios from 'axios'

// Use Next.js public env variable with a sane default
const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

console.log('[API Client] Initialized with baseURL:', baseURL)

// Simple response cache for dashboard APIs
const responseCache = new Map()
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes cache

const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
  timeout: 120000, // 120 second timeout (tăng từ 30s để xử lý dữ liệu lớn)
})

// Add request interceptor for debugging and caching
apiClient.interceptors.request.use(
  (config) => {
    // Check cache for GET requests
    if (config.method === 'get') {
      const cacheKey = `${config.baseURL}${config.url}`
      const cached = responseCache.get(cacheKey)
      if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
        console.log('[API Cache Hit]', config.url)
        return Promise.reject({
          __fromCache: true,
          data: cached.response
        })
      }
    }
    console.log('[API Request]', config.method?.toUpperCase(), config.baseURL + config.url)
    return config
  },
  (error) => {
    if (error.__fromCache) {
      return error
    }
    console.error('[API Request Error]', error.message)
    return Promise.reject(error)
  }
)

// Add response interceptor for debugging and error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log('[API Response]', response.status, response.config.url, '- Response time:', response.headers['x-response-time'] || 'N/A')
    
    // Cache successful GET responses
    if (response.config.method === 'get') {
      const cacheKey = `${response.config.baseURL}${response.config.url}`
      responseCache.set(cacheKey, {
        response: response.data,
        timestamp: Date.now()
      })
    }
    
    return response
  },
  (error) => {
    // Handle cache hit errors
    if (error.__fromCache) {
      return Promise.resolve({
        data: error.data,
        status: 200,
        statusText: 'OK (from cache)',
        headers: {},
        config: {},
        cached: true
      })
    }

    if (error.response) {
      // Server responded with error status
      console.error('[API Error Response]', error.response.status, error.response.statusText)
      console.error('[API Response Data]', error.response.data)
    } else if (error.request) {
      // Request made but no response received
      console.error('[API No Response]', 'No response from server', error.message)
      console.error('[API Request URL]', error.config?.baseURL + error.config?.url)
      console.error('[API Code]', error.code)
      
      // Nếu timeout, gợi ý kiểm tra backend
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        console.warn('[API Timeout Warning] Backend có thể chậm. Hãy kiểm tra:')
        console.warn('  - Docker services: docker-compose ps')
        console.warn('  - Backend health: http://localhost:8000/api/admin/health')
        console.warn('  - Logs: docker-compose logs backend --tail=50')
      }
    } else {
      // Error in request setup
      console.error('[API Error]', error.message)
    }
    return Promise.reject(error)
  }
)

export default apiClient
