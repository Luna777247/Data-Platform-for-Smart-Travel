'use client'

import { ReactNode } from 'react'
import { BackToHomeButton } from '@/components/ui/back-to-home-button'

interface PageLayoutProps {
  children: ReactNode
  title?: string
  description?: string
  showBackButton?: boolean
  headerActions?: ReactNode
  className?: string
  icon?: ReactNode
}

export function PageLayout({
  children,
  title,
  description,
  showBackButton = false,
  headerActions,
  className = '',
  icon
}: PageLayoutProps) {
  return (
    <div className={`min-h-screen bg-gradient-to-br from-background via-background to-muted/20 ${className}`} suppressHydrationWarning={true}>
      {/* Enhanced Header Section */}
      {(title || showBackButton || headerActions) && (
        <div className="border-b border-border/40 bg-gradient-to-r from-slate-50/50 to-transparent dark:from-slate-950/50 backdrop-blur-sm" suppressHydrationWarning={true}>
          <div className="container mx-auto px-4 py-6 sm:py-8" suppressHydrationWarning={true}>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4" suppressHydrationWarning={true}>
              <div className="flex items-center gap-4 min-w-0 flex-1" suppressHydrationWarning={true}>
                {showBackButton && <BackToHomeButton />}
                <div className="min-w-0 flex-1" suppressHydrationWarning={true}>
                  <div className="flex items-center gap-3 mb-2" suppressHydrationWarning={true}>
                    {icon && (
                      <div className="flex-shrink-0">
                        {icon}
                      </div>
                    )}
                    {title && (
                      <h1 className="text-2xl sm:text-4xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-slate-900 to-slate-700 dark:from-slate-100 dark:to-slate-300 truncate" suppressHydrationWarning={true}>
                        {title}
                      </h1>
                    )}
                  </div>
                  {description && (
                    <p className="text-sm sm:text-base text-muted-foreground line-clamp-2" suppressHydrationWarning={true}>
                      {description}
                    </p>
                  )}
                </div>
              </div>
              {headerActions && (
                <div className="flex items-center gap-2 flex-shrink-0" suppressHydrationWarning={true}>
                  {headerActions}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8" suppressHydrationWarning={true}>
        <main suppressHydrationWarning={true}>
          {children}
        </main>
      </div>
    </div>
  )
}
