import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export const fetchMetrics = () => api.get('/dashboard/metrics').then(r => r.data)
export const fetchActivity = (limit = 30) => api.get(`/dashboard/activity?limit=${limit}`).then(r => r.data)
export const fetchFraudFlags = () => api.get('/fraud/flags').then(r => r.data)
export const fetchUserGraph = (userId, depth = 3) =>
  api.get(`/referral/user/${userId}/graph?depth=${depth}`).then(r => r.data)
export const fetchUsers = () => api.get('/users/?limit=100').then(r => r.data)
export const fetchUserRewards = (userId) => api.get(`/user/${userId}/rewards`).then(r => r.data)
export const claimReferral = (data) => api.post('/referral/claim', data).then(r => r.data)
export const createUser = (data) => api.post('/users/', data).then(r => r.data)
export const runSimulation = (data) => api.post('/dashboard/simulate', data).then(r => r.data)

export default api
