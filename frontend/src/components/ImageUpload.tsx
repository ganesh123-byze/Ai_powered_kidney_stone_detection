import React, { useCallback, useState } from 'react';
import { useDropzone, FileRejection } from 'react-dropzone';

interface ImageUploadProps {
  onImageSelect: (file: File) => void;
  disabled?: boolean;
  maxSize?: number; // in bytes
}

const ImageUpload: React.FC<ImageUploadProps> = ({
  onImageSelect,
  disabled = false,
  maxSize = 10 * 1024 * 1024, // 10MB default
}) => {
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[], fileRejections: FileRejection[]) => {
      setError(null);

      // Handle rejections
      if (fileRejections.length > 0) {
        const rejection = fileRejections[0];
        if (rejection.errors[0]?.code === 'file-too-large') {
          setError(`File is too large. Maximum size is ${Math.round(maxSize / 1024 / 1024)}MB`);
        } else if (rejection.errors[0]?.code === 'file-invalid-type') {
          setError('Invalid file type. Please upload an image (JPEG, PNG, BMP, TIFF)');
        } else {
          setError(rejection.errors[0]?.message || 'Invalid file');
        }
        return;
      }

      // Handle accepted file
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        setFileName(file.name);

        // Create preview
        const reader = new FileReader();
        reader.onloadend = () => {
          setPreview(reader.result as string);
        };
        reader.readAsDataURL(file);

        // Notify parent
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

  return (
    <div className="w-full">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
          transition-all duration-200 ease-in-out
          ${disabled ? 'opacity-50 cursor-not-allowed bg-gray-50' : ''}
          ${isDragActive && !isDragReject ? 'border-primary-500 bg-primary-50' : ''}
          ${isDragReject ? 'border-red-500 bg-red-50' : ''}
          ${!isDragActive && !disabled ? 'border-gray-300 hover:border-primary-400 hover:bg-gray-50' : ''}
        `}
      >
        <input {...getInputProps()} />

        {preview ? (
          // Preview State
          <div className="space-y-4">
            <div className="relative inline-block">
              <img
                src={preview}
                alt="Preview"
                className="max-h-64 max-w-full rounded-lg shadow-md mx-auto"
              />
              {!disabled && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    clearImage();
                  }}
                  className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-600 transition-colors shadow-md"
                  aria-label="Remove image"
                >
                  ×
                </button>
              )}
            </div>
            <p className="text-sm text-gray-600 truncate max-w-xs mx-auto">
              {fileName}
            </p>
            <p className="text-xs text-gray-400">
              Click or drag to replace
            </p>
          </div>
        ) : (
          // Empty State
          <div className="space-y-4">
            {/* Upload Icon */}
            <div className="mx-auto w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
              <svg
                className="w-8 h-8 text-primary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            </div>

            {/* Text */}
            <div>
              <p className="text-lg font-medium text-gray-700">
                {isDragActive ? 'Drop the image here' : 'Drag & drop an ultrasound image'}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                or <span className="text-primary-600 font-medium">browse</span> to choose a file
              </p>
            </div>

            {/* Supported formats */}
            <p className="text-xs text-gray-400">
              Supports: JPEG, PNG, BMP, TIFF (max {Math.round(maxSize / 1024 / 1024)}MB)
            </p>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600 flex items-center gap-2">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            {error}
          </p>
        </div>
      )}
    </div>
  );
};

export default ImageUpload;
