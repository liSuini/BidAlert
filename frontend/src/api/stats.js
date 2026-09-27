import api from './client'

export const statsApi = {
  overview: () => api.get('/stats/overview'),
  stages: () => api.get('/stats/stages'),
  regions: () => api.get('/stats/regions'),
  overdue: (limit = 5) => api.get('/stats/overdue', { params: { limit } }),
}
