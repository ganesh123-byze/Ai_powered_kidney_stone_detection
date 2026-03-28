import React from 'react';
import { PredictionResponse, SeverityLevel } from '../types/types';

interface PredictionResultProps {
  result: PredictionResponse;
  onReset?: () => void;
}

const PredictionResult: React.FC<PredictionResultProps> = ({ result, onReset }) => {
  // Status color mapping for binary stone detection
  const getSeverityConfig = (severity: string): { 
    bgColor: string; 
    textColor: string; 
    borderColor: string;
    icon: string;
  } => {
    const severityLower = severity.toLowerCase() as Lowercase<SeverityLevel>;
    
    switch (severityLower) {
      case 'normal':
        return {
          bgColor: 'bg-green-50',
          textColor: 'text-green-700',
          borderColor: 'border-green-200',
          icon: '✓',
        };
      case 'detected':
        return {
          bgColor: 'bg-red-50',
          textColor: 'text-red-700',
          borderColor: 'border-red-200',
          icon: '⚠',
        };
      default:
        return {
          bgColor: 'bg-gray-50',
          textColor: 'text-gray-700',
          borderColor: 'border-gray-200',
          icon: '?',
        };
    }
  };

  const severityConfig = getSeverityConfig(result.severity);
  const confidencePercent = Math.round(result.confidence * 100);

  // Confidence color based on value
  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.9) return 'text-green-600';
    if (confidence >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="w-full space-y-4 animate-fadeIn">
      {/* Main Result Card */}
      <div className={`${severityConfig.bgColor} ${severityConfig.borderColor} border-2 rounded-xl p-6 shadow-sm`}>
        {/* Header with severity badge */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800">Prediction Result</h3>
          <span
            className={`${severityConfig.bgColor} ${severityConfig.textColor} ${severityConfig.borderColor} 
              border px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1`}
          >
            <span>{severityConfig.icon}</span>
            {result.severity}
          </span>
        </div>

        {/* Predicted Class */}
        <div className="mb-6">
          <p className="text-sm text-gray-500 mb-1">Predicted Condition</p>
          <p className="text-2xl font-bold text-gray-900">{result.class}</p>
        </div>

        {/* Confidence Meter */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">Confidence</p>
            <p className={`text-lg font-bold ${getConfidenceColor(result.confidence)}`}>
              {confidencePercent}%
            </p>
          </div>
          
          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ease-out ${
                result.confidence >= 0.9
                  ? 'bg-green-500'
                  : result.confidence >= 0.7
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
              style={{ width: `${confidencePercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* All Probabilities (if available) */}
      {result.all_probabilities && (
        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">All Class Probabilities</h4>
          <div className="space-y-2">
            {Object.entries(result.all_probabilities)
              .sort(([, a], [, b]) => b - a)
              .map(([className, prob]) => (
                <div key={className} className="flex items-center gap-3">
                  <span className="text-sm text-gray-600 w-32 truncate">{className}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full bg-primary-500 rounded-full"
                      style={{ width: `${Math.round(prob * 100)}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-500 w-12 text-right">
                    {Math.round(prob * 100)}%
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {onReset && (
        <div className="flex justify-center pt-2">
          <button
            onClick={onReset}
            className="px-6 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 
              rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-colors duration-200
              flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Analyze Another Image
          </button>
        </div>
      )}

      {/* Disclaimer */}
      <p className="text-xs text-gray-400 text-center mt-4">
        ⚕️ This is an AI-assisted analysis tool. Always consult a qualified healthcare professional for diagnosis.
      </p>
    </div>
  );
};

export default PredictionResult;
