/**
 * Type definitions for Kidney Stone Detection API
 * Binary classification: Normal vs Stone
 */

export interface PredictionResponse {
  success: boolean;
  class: string;  // 'Normal' or 'stone'
  confidence: number;
  severity: string;  // 'Normal' or 'Detected'
  class_index?: number;  // 0 = Normal, 1 = stone
  all_probabilities?: Record<string, number>;
  gradcam?: {
    heatmap: number[][];
    overlay: number[][][];
  };
}

export interface UploadResponse {
  success: boolean;
  filename: string;
  file_path: string;
  file_size: number;
  message: string;
}

export interface ErrorResponse {
  success: boolean;
  error: string;
  detail?: string;
}

export interface ModelInfo {
  loaded: boolean;
  model_path?: string;
  device?: string;
  num_classes?: number;
  class_names?: string[];
}

export interface HealthResponse {
  status: string;
  version: string;
  model_loaded: boolean;
  cuda_available: boolean;
  model_info?: ModelInfo;
}

export type SeverityLevel = 'Normal' | 'Detected' | 'Unknown';

export interface PredictionState {
  isLoading: boolean;
  result: PredictionResponse | null;
  error: string | null;
}
