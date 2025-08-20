import React from 'react';
import { clsx } from 'clsx';

export interface LoadingProps {
  variant?: 'spinner' | 'dots' | 'bars' | 'pulse';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  text?: string;
  fullScreen?: boolean;
  className?: string;
}

const Loading: React.FC<LoadingProps> = ({
  variant = 'spinner',
  size = 'md',
  text,
  fullScreen = false,
  className,
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12',
  };

  const renderSpinner = () => (
    <svg
      className={clsx('animate-spin', sizeClasses[size])}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );

  const renderDots = () => (
    <div className="flex space-x-1">
      <div
        className={clsx(
          'bg-current rounded-full animate-bounce',
          sizeClasses[size]
        )}
        style={{ animationDelay: '0ms' }}
      />
      <div
        className={clsx(
          'bg-current rounded-full animate-bounce',
          sizeClasses[size]
        )}
        style={{ animationDelay: '150ms' }}
      />
      <div
        className={clsx(
          'bg-current rounded-full animate-bounce',
          sizeClasses[size]
        )}
        style={{ animationDelay: '300ms' }}
      />
    </div>
  );

  const renderBars = () => (
    <div className="flex space-x-1">
      <div
        className={clsx(
          'bg-current animate-pulse',
          size === 'sm' ? 'w-1 h-3' : size === 'md' ? 'w-1 h-4' : size === 'lg' ? 'w-1.5 h-6' : 'w-2 h-8'
        )}
        style={{ animationDelay: '0ms' }}
      />
      <div
        className={clsx(
          'bg-current animate-pulse',
          size === 'sm' ? 'w-1 h-3' : size === 'md' ? 'w-1 h-4' : size === 'lg' ? 'w-1.5 h-6' : 'w-2 h-8'
        )}
        style={{ animationDelay: '150ms' }}
      />
      <div
        className={clsx(
          'bg-current animate-pulse',
          size === 'sm' ? 'w-1 h-3' : size === 'md' ? 'w-1 h-4' : size === 'lg' ? 'w-1.5 h-6' : 'w-2 h-8'
        )}
        style={{ animationDelay: '300ms' }}
      />
    </div>
  );

  const renderPulse = () => (
    <div
      className={clsx(
        'bg-current rounded-full animate-ping',
        sizeClasses[size]
      )}
    />
  );

  const renderLoader = () => {
    switch (variant) {
      case 'spinner':
        return renderSpinner();
      case 'dots':
        return renderDots();
      case 'bars':
        return renderBars();
      case 'pulse':
        return renderPulse();
      default:
        return renderSpinner();
    }
  };

  const content = (
    <div
      className={clsx(
        'flex flex-col items-center justify-center space-y-3',
        className
      )}
    >
      <div className="text-blue-600 dark:text-blue-400">
        {renderLoader()}
      </div>
      {text && (
        <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
          {text}
        </p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white dark:bg-slate-900 flex items-center justify-center z-50">
        {content}
      </div>
    );
  }

  return content;
};

export default Loading;

// Convenience components for common use cases
export const LoadingSpinner: React.FC<Omit<LoadingProps, 'variant'>> = (props) => (
  <Loading variant="spinner" {...props} />
);

export const LoadingDots: React.FC<Omit<LoadingProps, 'variant'>> = (props) => (
  <Loading variant="dots" {...props} />
);

export const LoadingBars: React.FC<Omit<LoadingProps, 'variant'>> = (props) => (
  <Loading variant="bars" {...props} />
);

export const LoadingPulse: React.FC<Omit<LoadingProps, 'variant'>> = (props) => (
  <Loading variant="pulse" {...props} />
);

export const LoadingFullScreen: React.FC<Omit<LoadingProps, 'fullScreen'>> = (props) => (
  <Loading fullScreen {...props} />
);
