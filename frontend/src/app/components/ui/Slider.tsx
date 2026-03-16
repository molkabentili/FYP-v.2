import * as RadixSlider from '@radix-ui/react-slider'

export function Slider({ value, onValueChange, min, max, step = 1 }: { value: number[]; onValueChange: (value: number[]) => void; min: number; max: number; step?: number }) {
  return (
    <RadixSlider.Root value={value} min={min} max={max} step={step} onValueChange={onValueChange} className="relative flex h-5 w-full items-center">
      <RadixSlider.Track className="relative h-2 grow rounded-full bg-gray-200">
        <RadixSlider.Range className="absolute h-full rounded-full bg-[var(--ooredoo-red)]" />
      </RadixSlider.Track>
      <RadixSlider.Thumb className="block h-5 w-5 rounded-full border-2 border-[var(--ooredoo-red)] bg-white shadow" />
    </RadixSlider.Root>
  )
}