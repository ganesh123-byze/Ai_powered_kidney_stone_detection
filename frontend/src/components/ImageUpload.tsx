import React, { useCallback, useState, useEffect } from 'react';
import { useDropzone, FileRejection } from 'react-dropzone';
import { getModelInfo } from '../api/api';

interface ImageUploadProps {
  onImageSelect: (file: File) => void;
  disabled?: boolean;
  maxSize?: number;
}

const ImageUpload: React.FC<ImageUploadProps> = ({
  onImageSelect,
  disabled = false,
  maxSize = 10 * 1024 * 1024,
}) => {
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [modelName, setModelName] = useState<string>('Loading...');

  const onDrop = useCallback(
    (acceptedFiles: File[], fileRejections: FileRejection[]) => {
      setError(null);

      if (fileRejections.length > 0) {
        const rejection = fileRejections[0];
        if (rejection.errors[0]?.code === 'file-too-large') {
          setError(`File too large. Max ${Math.round(maxSize / 1024 / 1024)}MB`);
        } else if (rejection.errors[0]?.code === 'file-invalid-type') {
          setError('Invalid file type. Use JPEG, PNG, BMP, or TIFF');
        } else {
          setError(rejection.errors[0]?.message || 'Invalid file');
        }
        return;
      }

      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        setFileName(file.name);

        const reader = new FileReader();
        reader.onloadend = () => {
          setPreview(reader.result as string);
        };
        reader.readAsDataURL(file);

        onImageSelect(file);
      }
    },
    [onImageSelect, maxSize]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/bmp': ['.bmp'],
      'image/tiff': ['.tiff', '.tif'],
    },
    maxSize,
    multiple: false,
    disabled,
  });

  const clearImage = () => {
    setPreview(null);
    setFileName(null);
    setError(null);
  };

  // Fetch model info on component mount
  useEffect(() => {
    const fetchModelInfo = async () => {
      try {
        const info = await getModelInfo();
        if (info.model_path) {
          // Extract model name from path (e.g., "best_model.onnx" or "best_model.pth")
          const pathParts = info.model_path.split('/');
          const fileName = pathParts[pathParts.length - 1];
          const modelBaseName = fileName.split('.')[0];
          // Convert to readable format (best_model -> Best Model)
          const readableName = modelBaseName
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
          setModelName(readableName);
        } else if (!info.loaded) {
          setModelName('No Model');
        }
      } catch (err) {
        setModelName('N/A');
        console.warn('Failed to fetch model info:', err);
      }
    };

    fetchModelInfo();
  }, []);

  return (
    <div className="w-full space-y-2.5">
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-lg transition-all duration-300 cursor-pointer
          p-6 sm:p-8 text-center group overflow-hidden
          ${disabled ? 'opacity-50 cursor-not-allowed bg-white/5 border-white/10' : ''}
          ${isDragActive && !isDragReject ? 'border-cyan-400 bg-cyan-500/20 scale-105' : ''}
          ${isDragReject ? 'border-red-400 bg-red-500/15' : ''}
          ${!isDragActive && !disabled ? 'border-white/20 hover:border-cyan-400 hover:bg-white/8' : ''}
          ${preview ? 'bg-gradient-to-br from-white/10 to-white/5' : 'bg-gradient-to-br from-white/6 to-blue-400/5'}
        `}
      >
        {/* Background accent */}
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/0 to-blue-500/0 group-hover:from-cyan-500/5 group-hover:to-blue-500/5 transition-all pointer-events-none" />
        
        <input {...getInputProps()} />

        {preview ? (
          // Preview State
          <div className="space-y-3 animate-fade-in relative z-10">
            <div className="flex flex-col sm:flex-row items-center gap-4">
              {/* Image */}
              <div className="relative">
                <img
                  src={preview}
                  alt="Preview"
                  className="max-h-48 max-w-xs rounded-lg shadow-lg border border-white/20 hover:scale-105 transition-transform"
                />
                {!disabled && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      clearImage();
                    }}
                    className="absolute -top-2 -right-2 bg-gradient-to-br from-red-500 to-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center hover:from-red-600 hover:to-red-700 transition-all font-bold text-xs shadow-md border border-red-400/50 hover:scale-110"
                    aria-label="Remove"
                  >
                    ✕
                  </button>
                )}
              </div>

              {/* Info */}
              <div className="text-left">
                <p className="text-sm text-green-300 font-semibold mb-1 flex items-center gap-1.5">
                  <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                  {modelName}
                </p>
                <p className="text-xs text-blue-200/70 truncate max-w-xs">{fileName}</p>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    clearImage();
                  }}
                  className="mt-2 text-xs text-cyan-400 hover:text-cyan-300 font-medium underline"
                >
                  Change image
                </button>
              </div>
            </div>
          </div>
        ) : (
          // Empty State
          <div className="space-y-3 animate-fade-in relative z-10">
            {/* Icon with animation */}
            <div className="flex justify-center">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-br from-cyan-400/20 to-blue-400/20 rounded-full blur-xl group-hover:scale-110 transition-transform" />
                <div className="relative text-5xl group-hover:scale-125 transition-transform origin-center">
                  {isDragActive ? '📥' : '📷'}
                </div>
              </div>
            </div>

            {/* Text */}
            <div>
              <p className="text-sm sm:text-base font-bold text-white mb-0.5">
                {isDragActive ? 'Drop here' : 'Upload Image'}
              </p>
              <p className="text-xs sm:text-sm text-blue-200/70">
                Drag or <span className="text-cyan-400 font-semibold">browse</span> ultrasound file
              </p>
            </div>

            {/* Formats */}
            <div className="flex flex-wrap gap-1.5 justify-center pt-1">
              {['JPG', 'PNG', 'BMP', 'TIFF'].map((fmt) => (
                <span key={fmt} className="text-xs bg-white/8 border border-white/15 rounded px-2 py-1 text-blue-200/70">
                  {fmt}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="backdrop-blur-sm bg-red-500/10 border border-red-400/30 rounded-lg p-2.5 flex gap-2 animate-slide-up">
          <span className="text-red-400 text-sm flex-shrink-0">✕</span>
          <p className="text-red-200/80 text-xs">{error}</p>
        </div>
      )}
    </div>
  );
};

export default ImageUpload;
