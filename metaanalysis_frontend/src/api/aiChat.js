import request from './request'

export function sendMessage(data) { return request.post('/api/ai/chat', data) }
export function getFields(datasetId) { return request.get(`/api/ai/fields/${datasetId}`) }
export function getConversations(params) { return request.get('/api/ai/conversations', { params }) }
export function getConversation(id) { return request.get(`/api/ai/conversations/${id}`) }
export function deleteConversation(id) { return request.delete(`/api/ai/conversations/${id}`) }
export function autoExplore(datasetId) { return request.post(`/api/ai/auto-explore/${datasetId}`) }
