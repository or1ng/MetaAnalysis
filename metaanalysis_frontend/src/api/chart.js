import request from './request'

export function generateChart(data) { return request.post('/api/chart/generate', data) }
export function getChartTemplates() { return request.get('/api/chart/templates') }
export function getChartFields(datasetId) { return request.get(`/api/chart/fields/${datasetId}`) }
export function batchCharts(data) { return request.post('/api/chart/batch', data) }
export function saveChart(data) { return request.post('/api/chart/save', data) }
export function getSavedCharts(datasetId) { return request.get(`/api/chart/saved/${datasetId}`) }
