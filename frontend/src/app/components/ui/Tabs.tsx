import * as RadixTabs from '@radix-ui/react-tabs'
import { ReactNode } from 'react'

export function Tabs({ value, onValueChange, children }: { value: string; onValueChange: (value: string) => void; children: ReactNode }) {
  return (
    <RadixTabs.Root value={value} onValueChange={onValueChange}>
      {children}
    </RadixTabs.Root>
  )
}

export const TabsList = RadixTabs.List
export const TabsTrigger = RadixTabs.Trigger
export const TabsContent = RadixTabs.Content