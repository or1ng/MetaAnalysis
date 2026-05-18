import request from './request'

export function autoClean(datasetId) { return request.post(`/api/clean/auto/${datasetId}`) }
export function customClean(datasetId, data) { return request.post(`/api/clean/custom/${datasetId}`, data) }
export function getCleanLogs(datasetId, params) { return request.get(`/api/clean/logs/${datasetId}`, { params }) }
export function rollbackClean(logId) { return request.post(`/api/clean/rollback/${logId}`) }
export function restoreDataset(datasetId) { return request.post(`/api/clean/restore/${datasetId}`) }
export function getCleanSummary(datasetId) { return request.get(`/api/clean/summary/${datasetId}`) }
export function getCleanPreview(datasetId, params) { return request.get(`/api/clean/preview/${datasetId}`, { params }) }
