import React from 'react';

interface LoaderProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  fullScreen?: boolean;
}

const Loader: React.FC<LoaderProps> = ({
  size = 'md',
  text = 'Loading...',
  fullScreen = false,
}) => {
  const sizeClasses = {
    sm: 'w-5 h-5 border-2',
    md: 'w-10 h-10 border-2.5',
    lg: 'w-14 h-14 border-3',
  };

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  const spinner = (
    <div className="flex flex-col items-center justify-center gap-3 animate-fade-in">
      <div className="relative">
        <div
          className={`${sizeClasses[size]} border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin`}
          role="status"
          aria-label="Loading"
        />
      </div>

      {text && (
        <div className="text-center">
          <p className={`${textSizeClasses[size]} font-semibold text-cyan-300 animate-pulse`}>
            {text}
          </p>
          <div className="flex justify-center gap-1 mt-2">
            <span className="w-1 h-1 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
            <span className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
            <span className="w-1 h-1 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
          </div>
        </div>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-slate-900/90 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
        <div className="relative">
          <div className="absolute -inset-16 bg-gradient-radial from-cyan-400/10 to-transparent rounded-full blur-2xl" />
          <div className="relative">
            {spinner}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="backdrop-blur-sm bg-white/8 border border-white/15 p-8 rounded-xl">
      {spinner}
    </div>
  );
};

export default Loader;
