import React from 'react';
import { clsx } from 'clsx';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  variant?: 'default' | 'outlined' | 'filled';
  size?: 'sm' | 'md' | 'lg';
  error?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  label?: string;
  helperText?: string;
  fullWidth?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      variant = 'default',
      size = 'md',
      error = false,
      leftIcon,
      rightIcon,
      label,
      helperText,
      fullWidth = false,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

    const baseClasses = clsx(
      'transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed',
      {
        // Size variants
        'px-3 py-1.5 text-sm': size === 'sm',
        'px-4 py-2 text-sm': size === 'md',
        'px-4 py-3 text-base': size === 'lg',
        
        // Width
        'w-full': fullWidth,
        
        // Variant styles
        'bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg focus:border-blue-500 focus:ring-blue-500 dark:focus:ring-offset-slate-900': variant === 'default',
        'bg-transparent border border-slate-300 dark:border-slate-600 rounded-lg focus:border-blue-500 focus:ring-blue-500 dark:focus:ring-offset-slate-900': variant === 'outlined',
        'bg-slate-50 dark:bg-slate-700 border border-transparent rounded-lg focus:bg-white dark:focus:bg-slate-800 focus:border-blue-500 focus:ring-blue-500 dark:focus:ring-offset-slate-900': variant === 'filled',
        
        // Error state
        'border-red-500 focus:border-red-500 focus:ring-red-500': error,
        
        // Icon padding
        'pl-10': leftIcon,
        'pr-10': rightIcon,
      }
    );

    const inputClasses = clsx(
      baseClasses,
      'text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400',
      className
    );

    return (
      <div className={clsx('space-y-1', { 'w-full': fullWidth })}>
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            {label}
          </label>
        )}
        
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <div className="h-5 w-5 text-gray-400">
                {leftIcon}
              </div>
            </div>
          )}
          
          <input
            ref={ref}
            id={inputId}
            className={inputClasses}
            {...props}
          />
          
          {rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <div className="h-5 w-5 text-gray-400">
                {rightIcon}
              </div>
            </div>
          )}
        </div>
        
        {helperText && (
          <p
            className={clsx(
              'text-sm',
              error
                ? 'text-red-600 dark:text-red-400'
                : 'text-gray-500 dark:text-gray-400'
            )}
          >
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
