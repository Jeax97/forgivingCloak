import { cn } from '../../lib/utils'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning'
  className?: string
}

const variantClasses: Record<string, string> = {
  default: 'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]',
  secondary: 'bg-[hsl(var(--secondary))] text-[hsl(var(--secondary-foreground))]',
  destructive: 'bg-[hsl(var(--destructive))] text-[hsl(var(--destructive-foreground))]',
  outline: 'border border-[hsl(var(--border))] text-[hsl(var(--foreground))]',
  success: 'bg-green-500/15 text-green-700 dark:text-green-400',
  warning: 'bg-yellow-500/15 text-yellow-700 dark:text-yellow-400',
}

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors',
        variantClasses[variant],
        className,
      )}
    >
      {children}
    </span>
  )
}
