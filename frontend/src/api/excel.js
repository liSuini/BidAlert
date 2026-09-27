import api from './client'

export const excelApi = {
  import: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/excel/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  getTemplate: () => api.get('/excel/template', { responseType: 'blob' }),
  export: (data) => api.post('/excel/export', data, { responseType: 'blob' }),
}
