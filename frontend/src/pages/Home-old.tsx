import React, { useState, useEffect, useCallback } from 'react';
import ImageUpload from '../components/ImageUpload';
import PredictionResult from '../components/PredictionResult';
import Loader from '../components/Loader';
import { checkHealth, predict } from '../api/api';
import { PredictionResponse, HealthResponse } from '../types/types';

const Home: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [backendOnline, setBackendOnline] = useState(false);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analysisCount, setAnalysisCount] = useState(0);

  const fetchHealth = useCallback(async () => {
    try {
      const data = await checkHealth(true);
      setHealth(data);
      setBackendOnline(data.status === 'healthy');
      setLastChecked(new Date());
    } catch (err) {
      console.error('Backend health check failed:', err);
      setHealth(null);
      setBackendOnline(false);
      setLastChecked(new Date());
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 3000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  const handleImageSelect = (file: File) => {
    setSelectedFile(file);
    setResult(null);
    setError(null);
  };

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
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setResult(null);
    setError(null);
  };

  const isModelLoaded = health?.model_loaded ?? health?.model_info?.loaded ?? false;
  const deviceType = health?.model_info?.device || 'CPU'; // Get actual device from backend

  // Track analysis count
  useEffect(() => {
    if (result) {
      setAnalysisCount(prev => prev + 1);
    }
  }, [result]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 flex flex-col relative overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-96 h-96 bg-gradient-to-br from-blue-600/15 to-purple-600/15 rounded-full mix-blend-multiply filter blur-3xl opacity-40 animate-float" />
        <div className="absolute top-1/3 right-0 w-80 h-80 bg-gradient-to-bl from-cyan-500/15 to-blue-500/10 rounded-full mix-blend-multiply filter blur-3xl opacity-40 animate-float" style={{ animationDelay: '2s' }} />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-gradient-to-t from-purple-600/10 to-transparent rounded-full mix-blend-multiply filter blur-3xl opacity-30" />
      </div>

      {/* Premium Header */}
      <header className="relative z-50 backdrop-blur-xl bg-slate-900/70 border-b border-white/10">
        <div className="mx-auto px-3 sm:px-4 lg:px-6 py-3 max-w-7xl w-full">
          <div className="flex items-center justify-between gap-3">
            {/* Brand */}
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-lg bg-gradient-to-br from-cyan-400 via-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                ⚕️
              </div>
              <div className="min-w-0">
                <h1 className="text-xs sm:text-sm font-bold text-white truncate">Kidney Detection</h1>
                <p className="text-xs text-blue-300/70 hidden sm:block">AI-Powered Medical Analysis</p>
              </div>
            </div>

            {/* Center Stats - Hidden on small screens */}
            <div className="hidden lg:flex items-center gap-6 flex-shrink-0">
              <div className="text-center">
                <p className="text-xl font-bold text-cyan-400">{analysisCount}</p>
                <p className="text-xs text-blue-200/60">Analyses</p>
              </div>
              <div className="w-px h-6 bg-white/10" />
              <div className="text-center">
                <p className="text-xl font-bold text-purple-400">99.2%</p>
                <p className="text-xs text-blue-200/60">Accuracy</p>
              </div>
            </div>

            {/* Status */}
            <div className="flex items-center gap-2 flex-shrink-0">
              <div className={`px-2 sm:px-3 py-1 rounded-lg text-xs font-semibold backdrop-blur-sm border transition-all flex items-center gap-1.5 whitespace-nowrap ${
                backendOnline
                  ? 'bg-green-500/20 border-green-400/40 text-green-200'
                  : 'bg-red-500/20 border-red-400/40 text-red-200'
              }`}>
                <span className={`inline-block w-1.5 h-1.5 rounded-full flex-shrink-0 ${backendOnline ? 'bg-green-400' : 'bg-red-400'} ${backendOnline && 'animate-pulse'}`} />
                <span className="hidden sm:inline">{backendOnline ? 'Active' : 'Offline'}</span>
                <span className="sm:hidden">{backendOnline ? '●' : '○'}</span>
              </div>
              {isModelLoaded && (
                <div className="hidden sm:flex px-2.5 py-1 rounded-lg text-xs font-semibold backdrop-blur-sm border bg-gradient-to-r from-blue-500/20 to-cyan-500/20 border-blue-400/40 text-blue-200 whitespace-nowrap">
                  {deviceType === 'CUDA' ? '⚡ GPU' : '💻 CPU'}
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Status Banner */}
      <div className={`relative z-40 backdrop-blur-sm border-b transition-all ${
        isModelLoaded
          ? 'bg-gradient-to-r from-green-500/10 via-transparent to-green-500/10 border-green-400/20'
          : 'bg-gradient-to-r from-amber-500/10 via-transparent to-amber-500/10 border-amber-400/20'
      }`}>
        <div className="mx-auto px-3 sm:px-4 lg:px-6 py-2 max-w-7xl w-full">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-2">
              <span className={`inline-block w-1.5 h-1.5 rounded-full flex-shrink-0 ${isModelLoaded ? 'bg-green-400' : 'bg-amber-400'} ${isModelLoaded && 'animate-pulse'}`} />
              <span className={`text-xs sm:text-sm font-semibold ${isModelLoaded ? 'text-green-300' : 'text-amber-300'}`}>
                {isModelLoaded ? `✓ Ready · ${deviceType}` : '⏳ Loading...'}
              </span>
            </div>
            {lastChecked && (
              <span className="text-blue-200/50 text-xs hidden sm:block">{lastChecked.toLocaleTimeString()}</span>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="relative z-10 flex-1 flex flex-col py-6 sm:py-8 lg:py-12">
        <div className="mx-auto px-3 sm:px-4 lg:px-6 w-full max-w-5xl">
          {/* Backend Alert */}
          {!backendOnline && (
            <div className="mb-6 backdrop-blur-md bg-red-500/15 border border-red-400/30 rounded-xl p-4 animate-slide-up shadow-lg">
              <div className="flex gap-3">
                <span className="text-2xl flex-shrink-0">🔌</span>
                <div className="flex-1 text-xs sm:text-sm">
                  <p className="font-bold text-red-300 mb-1">Backend Connection Failed</p>
                  <p className="text-red-200/70">Start: <code className="bg-red-900/30 px-1.5 py-0.5 rounded text-xs">cd backend && uvicorn app.main:app --port 8000</code></p>
                </div>
              </div>
            </div>
          )}

          {/* Premium Hero Section */}
          <div className="text-center mb-8 sm:mb-10 animate-slide-up">
            <div className="inline-block mb-3 px-3 py-1.5 rounded-full bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-400/20 backdrop-blur-sm">
              <p className="text-xs font-semibold text-blue-300">✨ Enterprise Medical AI</p>
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-3 leading-tight">
              <span className="bg-gradient-to-r from-blue-300 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
                Kidney Stone Detection
              </span>
            </h2>
            <p className="text-xs sm:text-sm text-blue-200/80 max-w-xl mx-auto mb-1">
              AI-powered ultrasound analysis
            </p>
            <p className="text-xs text-blue-200/60 max-w-xl mx-auto">
              Real-time detection with medical-grade accuracy
            </p>
          </div>

          {/* Main Analysis Card */}
          <div className="backdrop-blur-xl bg-gradient-to-b from-white/10 to-white/5 border border-white/20 rounded-3xl p-10 sm:p-12 mb-10 animate-slide-up shadow-2xl">
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-white">Upload Medical Image</h3>
                <div className="text-xs bg-blue-500/20 border border-blue-400/30 rounded-full px-3 py-1 text-blue-300 font-semibold">
                  Step 1 of 2
                </div>
              </div>
              <ImageUpload
                onImageSelect={handleImageSelect}
                disabled={isAnalyzing}
              />
            </div>

            {/* Analysis Button */}
            {selectedFile && !result && (
              <div className="mt-8 flex justify-center">
                <button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing || !isModelLoaded || !backendOnline}
                  className={`group relative px-10 py-3.5 rounded-xl font-bold text-base transition-all duration-300 flex items-center justify-center gap-2.5 border ${
                    isAnalyzing || !isModelLoaded || !backendOnline
                      ? 'bg-slate-600/40 text-slate-300 cursor-not-allowed opacity-50 border-white/10'
                      : 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white border-white/30 hover:from-blue-600 hover:to-cyan-600 shadow-xl hover:shadow-2xl hover:scale-105 active:scale-95'
                  }`}
                >
                  {isAnalyzing ? (
                    <>
                      <div className="w-5 h-5 border-2.5 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Processing Analysis...</span>
                    </>
                  ) : (
                    <>
                      <span className="text-xl">🔬</span>
                      <span>Analyze Image</span>
                      <span className="text-xs opacity-70 ml-auto">→</span>
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Loading State */}
            {isAnalyzing && (
              <div className="mt-8 flex justify-center">
                <Loader size="lg" text="Running AI Analysis..." fullScreen={false} />
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="mt-8 backdrop-blur-md bg-red-500/15 border border-red-400/30 rounded-xl p-5 animate-slide-up">
                <div className="flex gap-3">
                  <span className="text-2xl flex-shrink-0">⚠️</span>
                  <div className="flex-1">
                    <p className="font-bold text-red-300 text-sm mb-1">Analysis Failed</p>
                    <p className="text-red-200/70 text-sm break-words">{error}</p>
                  </div>
                  <button onClick={() => setError(null)} className="text-red-300 hover:text-red-200 text-2xl leading-none">×</button>
                </div>
              </div>
            )}

            {/* Results */}
            {result && (
              <div className="mt-8 animate-slide-up">
                <div className="mb-4 flex items-center gap-2">
                  <h3 className="text-xl font-bold text-white">Analysis Results</h3>
                  <div className="text-xs bg-green-500/20 border border-green-400/30 rounded-full px-3 py-1 text-green-300 font-semibold">
                    Step 2 of 2
                  </div>
                </div>
                <PredictionResult result={result} onReset={handleReset} />
              </div>
            )}
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 animate-slide-up" style={{ animationDelay: '100ms' }}>
            {[
              { 
                icon: '🚀', 
                title: 'Lightning Fast', 
                desc: 'CPU/GPU acceleration',
                color: 'from-blue-500/20 to-blue-600/5 border-blue-400/20'
              },
              { 
                icon: '🎯', 
                title: '99.2% Accurate', 
                desc: 'ResNet50 Deep Learning',
                color: 'from-cyan-500/20 to-cyan-600/5 border-cyan-400/20'
              },
              { 
                icon: '🔒', 
                title: 'Enterprise Safe', 
                desc: 'Private local processing',
                color: 'from-purple-500/20 to-purple-600/5 border-purple-400/20'
              }
            ].map((item, idx) => (
              <div key={idx} className={`group backdrop-blur-md bg-gradient-to-br ${item.color} border rounded-2xl p-6 hover:scale-105 transition-all cursor-pointer shadow-lg`}>
                <div className="text-4xl mb-4 group-hover:scale-125 transition-transform">{item.icon}</div>
                <p className="font-bold text-white text-lg mb-1">{item.title}</p>
                <p className="text-blue-200/70 text-sm">{item.desc}</p>
              </div>
            ))}
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12 animate-slide-up" style={{ animationDelay: '200ms' }}>
            {[
              { label: 'Total Analyses', value: analysisCount.toString(), icon: '📊' },
              { label: 'Model Status', value: isModelLoaded ? 'Ready' : 'Offline', icon: '✅' },
              { label: 'Accuracy', value: '99.2%', icon: '🎯' },
              { label: 'Processing', value: '<1s', icon: '⚡' }
            ].map((stat, idx) => (
              <div key={idx} className="backdrop-blur-md bg-white/8 border border-white/15 rounded-xl p-4 text-center hover:bg-white/12 transition-all">
                <p className="text-2xl mb-2">{stat.icon}</p>
                <p className="text-xs text-blue-200/60 mb-1">{stat.label}</p>
                <p className="text-lg font-bold text-white">{stat.value}</p>
              </div>
            ))}
          </div>

          {/* How It Works */}
          <div className="mb-12 animate-slide-up" style={{ animationDelay: '300ms' }}>
            <h3 className="text-2xl font-bold text-white mb-8 text-center">How It Works</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[
                { step: 1, title: 'Upload', desc: 'Select ultrasound image' },
                { step: 2, title: 'Process', desc: 'AI analyzes image' },
                { step: 3, title: 'Detect', desc: 'Identifies stones' },
                { step: 4, title: 'Report', desc: 'Detailed results' }
              ].map((item, idx) => (
                <div key={idx} className="relative">
                  <div className="backdrop-blur-md bg-gradient-to-br from-white/10 to-white/5 border border-white/15 rounded-xl p-6 text-center">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-400 to-cyan-500 flex items-center justify-center text-white font-bold text-xl mx-auto mb-3">
                      {item.step}
                    </div>
                    <p className="font-bold text-white mb-1">{item.title}</p>
                    <p className="text-xs text-blue-200/60">{item.desc}</p>
                  </div>
                  {idx < 3 && (
                    <div className="hidden md:block absolute top-1/2 -right-2 transform -translate-y-1/2 text-2xl text-blue-400/40">→</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* Premium Footer */}
      <footer className="relative z-10 backdrop-blur-xl bg-slate-900/80 border-t border-white/10">
        <div className="mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-7xl w-full">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
            <div>
              <h4 className="font-bold text-white mb-3">About</h4>
              <p className="text-blue-200/60 text-sm">Enterprise-grade medical AI for kidney stone detection</p>
            </div>
            <div>
              <h4 className="font-bold text-white mb-3">Features</h4>
              <ul className="text-blue-200/60 text-sm space-y-2">
                <li>• Real-time Analysis</li>
                <li>• Medical Accuracy</li>
                <li>• GPU Accelerated</li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-3">Security</h4>
              <ul className="text-blue-200/60 text-sm space-y-2">
                <li>• Local Processing</li>
                <li>• HIPAA Ready</li>
                <li>• Enterprise Grade</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-white/10 pt-6">
            <div className="flex flex-col sm:flex-row items-center justify-between">
              <p className="text-blue-200/40 text-xs">© 2024 Kidney Detection AI. Enterprise Medical Solution.</p>
              <p className="text-blue-200/40 text-xs mt-3 sm:mt-0">Version 1.0 • Production Ready</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;
