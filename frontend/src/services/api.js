import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

export const linkApi = {
  save: (url, notes = '') =>
    api.post('/links/', { url, notes: notes || undefined }).then(r => r.data),

  list: (filters = {}) => {
    const params = {}
    if (filters.status) params.status = filters.status
    if (filters.category) params.category = filters.category
    return api.get('/links/', { params }).then(r => r.data)
  },

  get: (id) => api.get(`/links/${id}`).then(r => r.data),

  update: (id, data) => api.patch(`/links/${id}`, data).then(r => r.data),

  delete: (id) => api.delete(`/links/${id}`).then(r => r.data),

  syncExpired: () => api.post('/links/sync-expired').then(r => r.data),
}
