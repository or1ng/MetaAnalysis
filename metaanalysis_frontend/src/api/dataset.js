import request from './request'

export function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/api/datasets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getDatasets(params) { return request.get('/api/datasets/', { params }) }
export function getDataset(id) { return request.get(`/api/datasets/${id}`) }
export function renameDataset(id, data) { return request.put(`/api/datasets/${id}`, data) }
export function deleteDataset(id) { return request.delete(`/api/datasets/${id}`) }
export function getDatasetPreview(id, params) { return request.get(`/api/datasets/${id}/preview`, { params }) }
export function getDatasetStats(id) { return request.get(`/api/datasets/${id}/stats`) }
