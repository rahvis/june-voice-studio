import React from 'react';
import { clsx } from 'clsx';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'outlined' | 'filled';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      className,
      variant = 'default',
      padding = 'md',
      hover = false,
      children,
      ...props
    },
    ref
  ) => {
    const baseClasses = clsx(
      'rounded-xl transition-all duration-200',
      {
        // Variant styles
        'bg-white dark:bg-slate-800 shadow-sm': variant === 'default',
        'bg-white dark:bg-slate-800 shadow-lg': variant === 'elevated',
        'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700': variant === 'outlined',
        'bg-slate-50 dark:bg-slate-700/50': variant === 'filled',
        
        // Padding variants
        'p-0': padding === 'none',
        'p-3': padding === 'sm',
        'p-6': padding === 'md',
        'p-8': padding === 'lg',
        
        // Hover effects
        'hover:shadow-md hover:-translate-y-1': hover && variant === 'default',
        'hover:shadow-xl hover:-translate-y-1': hover && variant === 'elevated',
        'hover:border-slate-300 dark:hover:border-slate-600': hover && variant === 'outlined',
        'hover:bg-slate-100 dark:hover:bg-slate-700': hover && variant === 'filled',
      }
    );

    return (
      <div
        ref={ref}
        className={clsx(baseClasses, className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

// Card sub-components
export const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={clsx('flex flex-col space-y-1.5', className)}
    {...props}
  />
));

CardHeader.displayName = 'CardHeader';

export const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={clsx('text-lg font-semibold leading-none tracking-tight text-gray-900 dark:text-white', className)}
    {...props}
  />
));

CardTitle.displayName = 'CardTitle';

export const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={clsx('text-sm text-gray-600 dark:text-gray-400', className)}
    {...props}
  />
));

CardDescription.displayName = 'CardDescription';

export const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={clsx('pt-0', className)}
    {...props}
  />
));

CardContent.displayName = 'CardContent';

export const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={clsx('flex items-center pt-6', className)}
    {...props}
  />
));

CardFooter.displayName = 'CardFooter';

export default Card;
