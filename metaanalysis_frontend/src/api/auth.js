import request from './request'

export function login(data) { return request.post('/api/auth/login', data) }
export function register(data) { return request.post('/api/auth/register', data) }
export function refreshToken(data) { return request.post('/api/auth/refresh', data) }
export function getUserInfo() { return request.get('/api/auth/me') }
