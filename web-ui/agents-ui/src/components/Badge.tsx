import clsx from 'clsx';
import { PropsWithChildren } from 'react';

type BadgeVariant = 'default' | 'muted';

interface BadgeProps extends PropsWithChildren {
  variant?: BadgeVariant;
  className?: string;
}

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide',
        variant === 'default'
          ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/60 dark:text-indigo-100'
          : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-200',
        className
      )}
    >
      {children}
    </span>
  );
}
