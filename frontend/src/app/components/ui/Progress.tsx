export function Progress({ value, color = '#cd2027' }: { value: number; color?: string }) {
  return (
    <div className="h-2 w-full rounded-full bg-gray-200">
      <div className="h-2 rounded-full" style={{ width: `${value}%`, backgroundColor: color }} />
    </div>
  )
}