import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/Tabs'
import { Card } from '../components/ui/Card'
import { DashboardPage } from './DashboardPage.tsx'
import { ProfilesPage } from './ProfilesPage.tsx'
import { StrategyPage } from './StrategyPage.tsx'

export function ResultsPage() {
  const [tab, setTab] = useState('profiles')
  const runId = sessionStorage.getItem('smartseg_run_id')

  return (
    <div className="container-page space-y-4">
      <h2 className="text-2xl font-bold">Customer Segmentation Results</h2>
      {runId && (
        <Card className="bg-blue-50">
          <p className="text-sm text-blue-800">
            Segmentation run completed: {runId.slice(0, 12)}... | Showing latest backend clustering output.
          </p>
        </Card>
      )}
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="grid w-full grid-cols-1 gap-2 rounded-lg bg-gray-100 p-1 md:grid-cols-3">
          <TabsTrigger value="profiles" className="rounded-md px-3 py-2 text-sm data-[state=active]:bg-white">Segment Profiles</TabsTrigger>
          <TabsTrigger value="strategy" className="rounded-md px-3 py-2 text-sm data-[state=active]:bg-white">Business Strategy</TabsTrigger>
          <TabsTrigger value="dashboard" className="rounded-md px-3 py-2 text-sm data-[state=active]:bg-white">Analytics Dashboard</TabsTrigger>
        </TabsList>
        <TabsContent value="profiles"><ProfilesPage /></TabsContent>
        <TabsContent value="strategy"><StrategyPage /></TabsContent>
        <TabsContent value="dashboard"><DashboardPage /></TabsContent>
      </Tabs>
    </div>
  )
}
