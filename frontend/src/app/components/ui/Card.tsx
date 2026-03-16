import { PropsWithChildren } from 'react'

export function Card({ children, className = '' }: PropsWithChildren<{ className?: string }>) {
  return <div className={`card ${className}`}>{children}</div>
}

export function CardTitle({ children, className = '' }: PropsWithChildren<{ className?: string }>) {
  return <h3 className={`text-lg font-semibold ${className}`}>{children}</h3>
}

export function CardDescription({ children, className = '' }: PropsWithChildren<{ className?: string }>) {
  return <p className={`text-sm text-slate-600 ${className}`}>{children}</p>
}