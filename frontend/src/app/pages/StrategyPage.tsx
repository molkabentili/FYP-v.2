import { Megaphone, Shield, Target, TrendingUp } from 'lucide-react'
import { useState } from 'react'
import { Card, CardTitle } from '../components/ui/Card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/Tabs'
import { segments, Segment } from '../data/mockData'
import { formatAtRiskChurn, getDisplaySegments, DisplaySegment, shouldShowChurnRisk } from '../../services/segmentTransform'

type StrategyBundle = {
  retention: string[]
  upselling: string[]
  campaigns: string[]
}

function buildDynamicStrategies(segment: { name: string; churnRiskPct: number; arpu: number; dataUsage: number; characteristics: string[] }) {
  const retention = [
    `Priority retention outreach for ${segment.name}`,
    shouldShowChurnRisk(segment)
      ? `Personalized save-offer based on At Risk churn (${formatAtRiskChurn(segment)})`
      : 'Standard lifecycle follow-up without displaying churn percentage',
    'Proactive support follow-up for recent service issues'
  ]

  const upselling = [
    segment.dataUsage > 30 ? 'Offer high-data bundle upgrades' : 'Offer right-sized hybrid voice-data plans',
    segment.arpu > 70 ? 'Introduce premium loyalty add-ons' : 'Offer value bundle with moderate ARPU lift',
    'Launch personalized next-best-offer recommendations'
  ]

  const campaigns = [
    `Run targeted campaign for ${segment.name}`,
    `Highlight key behavior patterns: ${segment.characteristics.slice(0, 2).join(' | ')}`,
    'Track conversion and retention impact weekly'
  ]

  return { retention, upselling, campaigns }
}

function getStrategiesForSegment(segment: DisplaySegment | Segment): StrategyBundle {
  // Check if the segment has a strategies property (i.e., it's a Segment from mock data)
  if ('strategies' in segment &&
      typeof segment.strategies === 'object' &&
      segment.strategies !== null &&
      Array.isArray((segment as Segment).strategies.retention) &&
      Array.isArray((segment as Segment).strategies.upselling) &&
      Array.isArray((segment as Segment).strategies.campaigns)
  ) {
    return segment.strategies as StrategyBundle
  }

  return buildDynamicStrategies(segment)
}

export function StrategyPage() {
  const [tab, setTab] = useState('retention')
  const dynamicSegments = getDisplaySegments()
  const activeSegments: (DisplaySegment | Segment)[] = dynamicSegments.length > 0 ? dynamicSegments : segments

  return (
    <div className="space-y-4 pt-4">
      <div className="grid gap-3 md:grid-cols-3">
        <Card className="bg-blue-50"><p className="mb-2 flex items-center gap-2 font-semibold text-blue-700"><Shield size={16} /> Retention</p><p className="text-sm">Loyalty focus and churn defense.</p></Card>
        <Card className="bg-green-50"><p className="mb-2 flex items-center gap-2 font-semibold text-green-700"><TrendingUp size={16} /> Upselling</p><p className="text-sm">Increase ARPU through bundle optimization.</p></Card>
        <Card className="bg-purple-50"><p className="mb-2 flex items-center gap-2 font-semibold text-purple-700"><Megaphone size={16} /> Campaigns</p><p className="text-sm">Targeted marketing initiatives by segment.</p></Card>
      </div>

      {activeSegments.map((segment) => {
        const strategies = getStrategiesForSegment(segment)
        return (
        <Card key={segment.id} className="border-l-4" style={{ borderLeftColor: segment.color }}>
          <div className="mb-3">
            <CardTitle className="text-base">{segment.name}</CardTitle>
            <p className="text-sm text-slate-600">{segment.customers.toLocaleString()} customers | ARPU {segment.arpu.toFixed(2)} DT/TND{shouldShowChurnRisk(segment) ? ` | At Risk churn ${formatAtRiskChurn(segment)}` : ''}</p>
          </div>
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="mb-3 flex gap-2 rounded-lg bg-gray-100 p-1">
              <TabsTrigger value="retention" className="rounded-md px-3 py-1.5 text-sm data-[state=active]:bg-white">Retention</TabsTrigger>
              <TabsTrigger value="upselling" className="rounded-md px-3 py-1.5 text-sm data-[state=active]:bg-white">Upselling</TabsTrigger>
              <TabsTrigger value="campaigns" className="rounded-md px-3 py-1.5 text-sm data-[state=active]:bg-white">Campaigns</TabsTrigger>
            </TabsList>
            <TabsContent value="retention"><NumberedList items={strategies.retention} color="blue" /></TabsContent>
            <TabsContent value="upselling"><NumberedList items={strategies.upselling} color="green" /></TabsContent>
            <TabsContent value="campaigns"><NumberedList items={strategies.campaigns} color="purple" /></TabsContent>
          </Tabs>
        </Card>
        )
      })}

      <Card>
        <CardTitle>Implementation Roadmap Q1 2026</CardTitle>
        <div className="mt-3 grid gap-3 md:grid-cols-3 text-sm">
          <RoadmapCard title="Phase 1 (Weeks 1-2)" subtitle="Critical Risk Mitigation" tone="blue" actions={['Launch At Risk save desk', 'Deploy complaint escalation loop']} />
          <RoadmapCard title="Phase 2 (Weeks 3-4)" subtitle="Premium Customer Engagement" tone="green" actions={['Activate VIP loyalty experiences', 'Pilot premium upsell bundles']} />
          <RoadmapCard title="Phase 3 (Weeks 5-8)" subtitle="Cross-Segment Growth" tone="purple" actions={['Scale campaign automation', 'Expand partner bundles', 'Optimize conversion funnels']} />
        </div>
      </Card>

      <Card>
        <CardTitle>KPIs & Success Metrics</CardTitle>
        <div className="mt-3 grid gap-3 md:grid-cols-2 text-sm">
          <ul className="list-disc space-y-1 pl-5">
            <li>Churn Rate Reduction: Target -10%</li>
            <li>ARPU Growth: Target +15%</li>
            <li>Customer Lifetime Value: Target +20%</li>
            <li>Net Promoter Score: Target 60+</li>
          </ul>
          <ul className="list-disc space-y-1 pl-5">
            <li>High Value: Retention &gt;95%, VIP enrollment &gt;80%</li>
            <li>Data Driven: 5G migration &gt;40%, bundles &gt;50%</li>
            <li>Budget: Postpaid migration &gt;15%, engagement &gt;60%</li>
            <li>At Risk: Win-back &gt;35%, resolution &gt;90%</li>
          </ul>
        </div>
      </Card>
    </div>
  )
}

function NumberedList({ items, color }: { items: string[]; color: 'blue' | 'green' | 'purple' }) {
  const tone = color === 'blue' ? 'bg-blue-50' : color === 'green' ? 'bg-green-50' : 'bg-purple-50'
  return <div className="grid gap-2 md:grid-cols-2">{items.map((item, i) => <div key={item} className={`rounded-lg p-3 text-sm ${tone}`}><span className="mr-2 font-semibold">{i + 1}.</span>{item}</div>)}</div>
}

function RoadmapCard({ title, subtitle, actions, tone }: { title: string; subtitle: string; actions: string[]; tone: 'blue' | 'green' | 'purple' }) {
  const badge = tone === 'blue' ? 'bg-blue-100 text-blue-700' : tone === 'green' ? 'bg-green-100 text-green-700' : 'bg-purple-100 text-purple-700'
  return (
    <div className="rounded-lg border border-gray-200 p-3">
      <span className={`rounded-full px-2 py-1 text-xs font-semibold ${badge}`}>{title}</span>
      <p className="mt-2 font-medium">{subtitle}</p>
      <ul className="mt-2 space-y-1 text-sm text-slate-700">{actions.map((action) => <li key={action} className="flex items-center gap-2"><Target size={14} />{action}</li>)}</ul>
    </div>
  )
}
