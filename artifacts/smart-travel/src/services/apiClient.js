import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || ''

const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
  timeout: 120000,
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('[API Error]', error.response.status, error.config?.url)
    } else if (error.request) {
      console.error('[API No Response]', error.message, error.config?.url)
    }
    return Promise.reject(error)
  }
)

export default apiClient
