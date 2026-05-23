import request from './request'

export function descriptive(data) { return request.post('/api/statistic/descriptive', data) }
export function hypothesis(data) { return request.post('/api/statistic/hypothesis', data) }
export function correlation(data) { return request.post('/api/statistic/correlation', data) }
export function regression(data) { return request.post('/api/statistic/regression', data) }
export function timeseries(data) { return request.post('/api/statistic/timeseries', data) }
export function clustering(data) { return request.post('/api/statistic/clustering', data) }
export function getFields(datasetId) { return request.get(`/api/statistic/fields/${datasetId}`) }
export function getColumnValues(datasetId, column) { return request.get(`/api/statistic/column-values/${datasetId}`, { params: { column } }) }

// P1 增强接口
export function logistic(data) { return request.post('/api/statistic/logistic', data) }
export function pca(data) { return request.post('/api/statistic/pca', data) }
export function dbscan(data) { return request.post('/api/statistic/dbscan', data) }
export function arima(data) { return request.post('/api/statistic/arima', data) }
