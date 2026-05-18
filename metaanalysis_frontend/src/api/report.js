import request from './request'

export function generateReport(data) { return request.post('/api/report/generate', data) }
export function getReports(params) { return request.get('/api/report/list', { params }) }
export function getReport(id) { return request.get(`/api/report/${id}`) }
export function previewReport(id) { return request.get(`/api/report/${id}/preview`) }
export function downloadReport(id) { return request.get(`/api/report/${id}/download`, { responseType: 'blob' }) }
export function deleteReport(id) { return request.delete(`/api/report/${id}`) }
