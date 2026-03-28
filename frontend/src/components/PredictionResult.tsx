import React from 'react';
import { PredictionResponse, SeverityLevel } from '../types/types';

interface PredictionResultProps {
  result: PredictionResponse;
  onReset?: () => void;
}

const PredictionResult: React.FC<PredictionResultProps> = ({ result, onReset }) => {
  const getSeverityConfig = (severity: string): {
    bgColor: string;
    textColor: string;
    icon: string;
  } => {
    const severityLower = severity.toLowerCase() as Lowercase<SeverityLevel>;
    return severityLower === 'normal'
      ? { bgColor: 'bg-green-500/15', textColor: 'text-green-300', icon: '✓' }
      : { bgColor: 'bg-red-500/15', textColor: 'text-red-300', icon: '⚠' };
  };

  const severityConfig = getSeverityConfig(result.severity);
  const confidencePercent = Math.round(result.confidence * 100);

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.9) return 'text-green-400';
    if (confidence >= 0.7) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="w-full space-y-4 animate-slide-up">
      {/* Result Header */}
      <div className="backdrop-blur-sm bg-white/8 border border-white/15 rounded-xl p-6 sm:p-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg sm:text-xl font-bold text-white">Analysis Result</h3>
          <span className={`px-3 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 backdrop-blur-sm border ${
            result.severity.toLowerCase() === 'normal'
              ? 'bg-green-500/20 border-green-400/40 text-green-300'
              : 'bg-red-500/20 border-red-400/40 text-red-300'
          }`}>
            <span>{severityConfig.icon}</span>
            {result.severity}
          </span>
        </div>

        {/* Prediction */}
        <div className="mb-6">
          <p className="text-xs text-blue-200/60 mb-1">Detected</p>
          <p className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-white to-blue-100 bg-clip-text text-transparent">
            {result.class}
          </p>
        </div>

        {/* Confidence */}
        <div className="space-y-3 bg-white/5 p-4 rounded-lg border border-white/10">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-blue-100">Confidence</p>
            <p className={`text-2xl font-bold ${getConfidenceColor(result.confidence)}`}>
              {confidencePercent}%
            </p>
          </div>

          <div className="relative w-full bg-white/10 rounded-full h-2.5 overflow-hidden border border-white/10">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                result.confidence >= 0.9
                  ? 'bg-gradient-to-r from-green-400 to-emerald-500'
                  : result.confidence >= 0.7
                  ? 'bg-gradient-to-r from-yellow-400 to-amber-500'
                  : 'bg-gradient-to-r from-orange-400 to-red-500'
              }`}
              style={{ width: `${confidencePercent}%` }}
            />
          </div>

          <div className="flex justify-between items-center text-xs text-blue-200/60">
            <span>
              {result.confidence >= 0.95 ? '🟢 Excellent' :
               result.confidence >= 0.85 ? '🟢 Very Good' :
               result.confidence >= 0.75 ? '🟡 Good' :
               result.confidence >= 0.60 ? '🟠 Fair' :
               '🔴 Low'}
            </span>
            <span>{(result.confidence * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>

      {/* Probabilities */}
      {result.all_probabilities && (
        <div className="backdrop-blur-sm bg-white/8 border border-white/15 rounded-xl p-6">
          <h4 className="font-bold text-white text-sm mb-4">📊 Class Probabilities</h4>
          <div className="space-y-3">
            {Object.entries(result.all_probabilities)
              .sort(([, a], [, b]) => b - a)
              .map(([className, prob], index) => (
                <div key={className}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-sm text-blue-100 font-medium">
                      {index + 1}. {className}
                    </span>
                    <span className="text-sm font-bold text-cyan-300">
                      {(Math.round(prob * 1000) / 10).toFixed(1)}%
                    </span>
                  </div>
                  <div className="relative w-full bg-white/5 rounded-full h-2 overflow-hidden border border-white/10">
                    <div
                      className="h-full bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full transition-all duration-500"
                      style={{ width: `${Math.round(prob * 100)}%` }}
                    />
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Actions */}
      {onReset && (
        <button
          onClick={onReset}
          className="w-full py-2.5 px-4 bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700 text-white font-semibold rounded-lg transition-all hover:shadow-lg text-sm border border-white/20"
        >
          Analyze Another Image
        </button>
      )}

      {/* Disclaimer */}
      <div className="backdrop-blur-sm bg-blue-500/10 border border-blue-400/20 rounded-lg p-3 text-center">
        <p className="text-xs text-blue-200/70 leading-relaxed">
          ⓘ For educational purposes only. Consult healthcare professionals for diagnosis.
        </p>
      </div>
    </div>
  );
};

export default PredictionResult;
