import React, { useState, useEffect, useCallback } from 'react';
import ImageUpload from '../components/ImageUpload';
import PredictionResult from '../components/PredictionResult';
import Loader from '../components/Loader';
import { checkHealth, predict } from '../api/api';
import { PredictionResponse, HealthResponse } from '../types/types';

const Home: React.FC = () => {
  // Backend status state
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [backendOnline, setBackendOnline] = useState(false);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  // UI state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch health status from backend
  const fetchHealth = useCallback(async () => {
    try {
      const data = await checkHealth(true);
      setHealth(data);
      setBackendOnline(data.status === 'healthy');
      setLastChecked(new Date());
    } catch (err) {
      console.error('Backend health check failed:', err);
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      console.error('Ensure backend is running: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload');
      setHealth(null);
      setBackendOnline(false);
      setLastChecked(new Date());
    }
  }, []);

  // Poll backend health every 3 seconds
  useEffect(() => {
    fetchHealth(); // Initial fetch
    const interval = setInterval(fetchHealth, 3000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  // Handle image selection
  const handleImageSelect = (file: File) => {
    setSelectedFile(file);
    setResult(null);
    setError(null);
  };

  // Handle prediction
  const handleAnalyze = async () => {
    if (!selectedFile) {
      setError('Please select an image first');
      return;
    }

    if (!health?.model_loaded) {
      setError('Model not loaded. Please load a model first via the backend.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setResult(null);

    try {
      const prediction = await predict(selectedFile, { returnAllProbs: true });
      setResult(prediction);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Prediction failed';
      // Extract detail from axios error if available
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Reset state
  const handleReset = () => {
    setSelectedFile(null);
    setResult(null);
    setError(null);
  };

  // Derived state
  const modelInfo = health?.model_info;
  const isModelLoaded = health?.model_loaded ?? health?.model_info?.loaded ?? false;
  const cudaAvailable = health?.cuda_available ?? false;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <header className="bg-white/90 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">Kidney Stone Detection</h1>
                <p className="text-xs text-gray-500">AI-Powered Ultrasound Analysis</p>
              </div>
            </div>

            {/* Status Indicators */}
            <div className="flex items-center gap-4 text-xs">
              {/* Backend Status */}
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100">
                <span className={`w-2 h-2 rounded-full ${backendOnline ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-gray-600">
                  {backendOnline ? 'Backend Online' : 'Backend Offline'}
                </span>
              </div>

              {/* CUDA Status */}
              {backendOnline && (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100">
                  <span className={`w-2 h-2 rounded-full ${cudaAvailable ? 'bg-green-500' : 'bg-yellow-500'}`} />
                  <span className="text-gray-600">
                    {cudaAvailable ? 'GPU Ready' : 'CPU Only'}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Model Status Banner */}
      <div className={`border-b ${isModelLoaded ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}`}>
        <div className="max-w-5xl mx-auto px-4 py-2">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              {isModelLoaded ? (
                <>
                  <span className="text-green-700 font-medium">✓ Model Loaded</span>
                  <span className="text-green-600">
                    | Classes: {modelInfo?.class_names?.join(', ') || 'Unknown'}
                    | Device: {modelInfo?.device || 'Unknown'}
                  </span>
                </>
              ) : (
                <span className="text-yellow-700 font-medium">
                  ⚠ No model loaded — Load a model via backend to enable predictions
                </span>
              )}
            </div>
            {lastChecked && (
              <span className="text-gray-400 text-xs">
                Last checked: {lastChecked.toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-10">
        {/* Backend Offline Alert */}
        {!backendOnline && (
          <div className="mb-8 p-4 bg-red-50 border border-red-300 rounded-xl">
            <div className="flex items-start gap-3">
              <span className="text-red-600 text-xl mt-0.5">⚠</span>
              <div className="flex-1">
                <h3 className="font-semibold text-red-800">Backend Not Connected</h3>
                <p className="text-sm text-red-700 mt-1">
                  Unable to reach the backend API at <code className="bg-red-100 px-2 py-0.5 rounded text-xs font-mono">http://localhost:8000</code>
                </p>
                <p className="text-sm text-red-700 mt-2">
                  <strong>To fix:</strong> Start the backend server in your terminal:
                </p>
                <code className="block bg-red-100 px-3 py-2 rounded text-xs font-mono mt-2 text-red-900">
                  cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
                </code>
              </div>
            </div>
          </div>
        )}
        
        {/* Title */}
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Kidney Stone Detection
          </h2>
          <p className="text-gray-600">
            Upload a kidney ultrasound image to detect the presence of kidney stones
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
          <div className="p-6">
            {/* Image Upload */}
            <ImageUpload
              onImageSelect={handleImageSelect}
              disabled={isAnalyzing}
            />

            {/* Analyze Button */}
            {selectedFile && !result && (
              <div className="mt-6 flex justify-center">
                <button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing || !isModelLoaded || !backendOnline}
                  className={`px-8 py-3 rounded-xl font-semibold text-white flex items-center gap-2 transition-all
                    ${isAnalyzing || !isModelLoaded || !backendOnline
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700 active:scale-95'
                    }`}
                >
                  {isAnalyzing ? (
                    <>
                      <Loader size="sm" text="" />
                      <span>Analyzing...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        />
                      </svg>
                      <span>Analyze Image</span>
                    </>
                  )}
                </button>

                {!isModelLoaded && backendOnline && (
                  <p className="text-xs text-yellow-600 mt-2 text-center">
                    Model must be loaded before analysis
                  </p>
                )}
              </div>
            )}

            {/* Loading State */}
            {isAnalyzing && (
              <div className="mt-6 text-center">
                <Loader size="lg" text="Analyzing ultrasound image..." />
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-xl">
                <div className="flex items-start gap-3">
                  <span className="text-red-500 text-xl">✕</span>
                  <div>
                    <h4 className="font-medium text-red-800">Analysis Failed</h4>
                    <p className="text-sm text-red-600 mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Result Display */}
            {result && (
              <div className="mt-6">
                <PredictionResult result={result} onReset={handleReset} />
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-3 border-t border-gray-100">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>API Version: {health?.version || 'Unknown'}</span>
              <span>
                {isModelLoaded
                  ? `${modelInfo?.num_classes || 2} classes | ${modelInfo?.device || 'auto'}`
                  : 'No model loaded'}
              </span>
            </div>
          </div>
        </div>

        {/* Info Cards */}
        <div className="mt-8 grid md:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mb-2">
              <span className="text-blue-600">1</span>
            </div>
            <h3 className="font-semibold text-gray-900 text-sm">Upload Image</h3>
            <p className="text-xs text-gray-500 mt-1">
              Drag & drop or browse to upload your kidney ultrasound image
            </p>
          </div>

          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mb-2">
              <span className="text-purple-600">2</span>
            </div>
            <h3 className="font-semibold text-gray-900 text-sm">AI Analysis</h3>
            <p className="text-xs text-gray-500 mt-1">
              ResNet50 model detects kidney stones in the ultrasound
            </p>
          </div>

          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mb-2">
              <span className="text-green-600">3</span>
            </div>
            <h3 className="font-semibold text-gray-900 text-sm">Get Results</h3>
            <p className="text-xs text-gray-500 mt-1">
              Normal or Stone detected with confidence scores
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-10">
        <div className="max-w-5xl mx-auto px-4 py-4 text-center text-xs text-gray-500">
          <p>© 2024 Kidney Stone Detection System — For educational purposes only</p>
        </div>
      </footer>
    </div>
  );
};

export default Home;
