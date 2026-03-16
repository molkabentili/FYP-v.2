import { PropsWithChildren } from 'react'

export function Badge({
  children,
  className = ''
}: PropsWithChildren<{ className?: string }>) {
  return <span className={`inline-flex rounded-full bg-gray-100 px-2.5 py-1 text-xs font-semibold ${className}`}>{children}</span>
}