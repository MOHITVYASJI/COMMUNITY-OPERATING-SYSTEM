/**
 * API Client for Community OS Backend
 */
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Clear token on unauthorized
      await AsyncStorage.removeItem('auth_token');
      await AsyncStorage.removeItem('user_data');
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  sendOTP: (phone: string) => api.post('/auth/send-otp', { phone }),
  verifyOTP: (phone: string, otp: string) => api.post('/auth/verify-otp', { phone, otp }),
  getMe: () => api.get('/auth/me'),
};

// Geography API
export const geoAPI = {
  getStates: () => api.get('/geo/states'),
  getDistricts: (stateId?: number) => api.get('/geo/districts', { params: { state_id: stateId } }),
  getZones: (districtId?: number) => api.get('/geo/zones', { params: { district_id: districtId } }),
  getColonies: (zoneId?: number) => api.get('/geo/colonies', { params: { zone_id: zoneId } }),
};

// User API
export const userAPI = {
  updateProfile: (data: any) => api.put('/users/profile', data),
};

// Admin API
export const adminAPI = {
  getStats: () => api.get('/admin/stats'),
  getSystemRules: () => api.get('/admin/system-rules'),
  createSystemRule: (data: any) => api.post('/admin/system-rules', data),
  getFeatureFlags: () => api.get('/admin/feature-flags'),
  createFeatureFlag: (data: any) => api.post('/admin/feature-flags', data),
};

// Events API
export const eventsAPI = {
  createEvent: (data: any) => api.post('/events', data),
  getEvents: (params?: any) => api.get('/events', { params }),
  getEvent: (id: number) => api.get(`/events/${id}`),
};

// Clubs API
export const clubsAPI = {
  createClub: (data: any) => api.post('/clubs', data),
  getClubs: (params?: any) => api.get('/clubs', { params }),
};

// Leaderboard API
export const leaderboardAPI = {
  getLeaderboard: (scope: string, geoId?: number, limit?: number) => 
    api.get('/leaderboard', { params: { scope, geo_id: geoId, limit } }),
};

export default api;
