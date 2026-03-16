import { PropsWithChildren } from 'react'

export function Table({ children }: PropsWithChildren) {
  return <table className="w-full text-left text-sm">{children}</table>
}

export function THead({ children }: PropsWithChildren) {
  return <thead className="border-b bg-gray-50">{children}</thead>
}

export function TBody({ children }: PropsWithChildren) {
  return <tbody>{children}</tbody>
}

export function TR({ children, className = '' }: PropsWithChildren<{ className?: string }>) {
  return <tr className={`border-b ${className}`}>{children}</tr>
}

export function TH({ children }: PropsWithChildren) {
  return <th className="px-3 py-2 text-xs font-semibold uppercase text-slate-600">{children}</th>
}

export function TD({ children, className = '' }: PropsWithChildren<{ className?: string }>) {
  return <td className={`px-3 py-2 ${className}`}>{children}</td>
}