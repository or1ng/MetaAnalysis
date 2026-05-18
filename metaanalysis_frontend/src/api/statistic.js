import request from './request'

export function descriptive(data) { return request.post('/api/statistic/descriptive', data) }
export function hypothesis(data) { return request.post('/api/statistic/hypothesis', data) }
export function correlation(data) { return request.post('/api/statistic/correlation', data) }
export function regression(data) { return request.post('/api/statistic/regression', data) }
export function timeseries(data) { return request.post('/api/statistic/timeseries', data) }
export function clustering(data) { return request.post('/api/statistic/clustering', data) }
export function getFields(datasetId) { return request.get(`/api/statistic/fields/${datasetId}`) }
