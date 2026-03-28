import axios from 'axios';
import { PredictionResponse, UploadResponse, ModelInfo, HealthResponse } from '../types/types';

// API base URL - defaults to localhost:8000
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 seconds for health checks
  headers: {
    'Accept': 'application/json',
  },
});

// Response interceptor for better error messages
api.interceptors.response.use(
  response => response,
  error => {
    if (error.message === 'Network Error' || error.code === 'ECONNABORTED') {
      // Network error - backend likely not running or not accessible
      console.warn(`Backend not accessible at ${API_BASE_URL}`);
      console.warn('Ensure backend is running: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload');
    }
    return Promise.reject(error);
  }
);

/**
 * Health check - GET /health
 * Returns backend status and optionally model info
 */
export async function checkHealth(includeModelInfo = true): Promise<HealthResponse> {
  const url = includeModelInfo ? '/health?include_model_info=true' : '/health';
  const response = await api.get<HealthResponse>(url);
  return response.data;
}

/**
 * Get model info - GET /model (root level, simpler)
 */
export async function getModelInfo(): Promise<ModelInfo> {
  const response = await api.get<ModelInfo>('/model');
  return response.data;
}

/**
 * Load model - POST /api/v1/predict/model/load
 */
export async function loadModel(modelPath: string, modelName = 'resnet50'): Promise<ModelInfo> {
  const response = await api.post<ModelInfo>('/api/v1/predict/model/load', {
    model_path: modelPath,
    model_name: modelName,
  });
  return response.data;
}

/**
 * Unload model - POST /api/v1/predict/model/unload
 */
export async function unloadModel(): Promise<{ success: boolean; message: string }> {
  const response = await api.post('/api/v1/predict/model/unload');
  return response.data;
}

/**
 * Upload image - POST /api/v1/upload
 */
export async function uploadImage(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post<UploadResponse>('/api/v1/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

/**
 * Predict - POST /api/v1/predict
 * Main prediction endpoint with options
 */
export async function predict(
  file: File,
  options: { returnAllProbs?: boolean; generateGradcam?: boolean } = {}
): Promise<PredictionResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  const params = new URLSearchParams();
  if (options.returnAllProbs) params.append('return_all_probs', 'true');
  if (options.generateGradcam) params.append('generate_gradcam', 'true');
  
  const url = `/api/v1/predict${params.toString() ? `?${params}` : ''}`;
  
  const response = await api.post<PredictionResponse>(url, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

/**
 * Quick predict - POST /predict (root level, simpler)
 */
export async function quickPredict(file: File): Promise<PredictionResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post<PredictionResponse>('/predict', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export default api;
