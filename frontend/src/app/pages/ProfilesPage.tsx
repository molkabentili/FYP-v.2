import { DollarSign, TrendingUp, Users } from 'lucide-react'
import { Card, CardTitle } from '../components/ui/Card'
import { Progress } from '../components/ui/Progress'
import { segments } from '../data/mockData'
import { Badge } from '../components/ui/Badge'
import { Table, TBody, TD, TH, THead, TR } from '../components/ui/Table'

export function ProfilesPage() {
  return (
    <div className="space-y-4 pt-4">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {segments.map((segment) => (
          <Card key={segment.id} className="border-t-4" style={{ borderTopColor: segment.color }}>
            <p className="text-sm font-semibold">{segment.name}</p>
            <p className="text-xs text-slate-600">{segment.customers.toLocaleString()} customers</p>
            <p className="mt-2 text-lg font-bold">${segment.arpu.toFixed(2)}</p>
            <p className="text-xs text-slate-600">ARPU</p>
            <div className="mt-2"><Progress value={segment.share} color={segment.color} /></div>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {segments.map((segment) => (
          <Card key={segment.id} className="border-l-4" style={{ borderLeftColor: segment.color }}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle className="text-base">{segment.name}</CardTitle>
              <Badge className={segment.churnRiskLabel === 'Low' ? 'bg-green-100 text-green-700' : segment.churnRiskLabel === 'Medium' ? 'bg-yellow-100 text-yellow-700' : segment.churnRiskLabel === 'High' ? 'bg-orange-100 text-orange-700' : 'bg-red-100 text-red-700'}>{segment.churnRiskLabel} ({segment.churnRiskPct}%)</Badge>
            </div>
            <p className="text-sm text-slate-600">{segment.customers.toLocaleString()} customers ({segment.share}%)</p>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <div className="space-y-2 text-sm">
                <p className="flex items-center gap-2"><DollarSign size={16} className="text-green-600" /> ARPU: ${segment.arpu.toFixed(2)}</p>
                <p className="flex items-center gap-2"><TrendingUp size={16} className="text-blue-600" /> Data: {segment.dataUsage} GB/mo</p>
                <p className="flex items-center gap-2"><TrendingUp size={16} className="text-purple-600" /> Voice: {segment.voiceMinutes} min/mo</p>
                <p className="flex items-center gap-2"><Users size={16} className="text-orange-600" /> Tenure: {segment.tenure} years</p>
              </div>
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                {segment.characteristics.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
          </Card>
        ))}
      </div>

      <Card>
        <CardTitle>Comparative Analysis</CardTitle>
        <div className="mt-3 overflow-x-auto">
          <Table>
            <THead><TR><TH>Segment</TH><TH>Customers</TH><TH>Market Share</TH><TH>ARPU</TH><TH>Data Usage</TH><TH>Voice</TH><TH>Tenure</TH><TH>Churn Risk</TH></TR></THead>
            <TBody>
              {segments.map((segment) => (
                <TR key={segment.id}>
                  <TD>{segment.name}</TD><TD>{segment.customers.toLocaleString()}</TD><TD>{segment.share}%</TD><TD>${segment.arpu.toFixed(2)}</TD><TD>{segment.dataUsage} GB</TD><TD>{segment.voiceMinutes}</TD><TD>{segment.tenure}</TD>
                  <TD><Badge className="bg-gray-100">{segment.churnRiskLabel}</Badge></TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </div>
      </Card>

      <Card>
        <CardTitle>Strategic Insights</CardTitle>
        <div className="mt-3 grid gap-3 md:grid-cols-2 text-sm">
          <div>
            <p className="font-semibold text-green-700">Revenue Opportunities</p>
            <ul className="mt-1 list-disc space-y-1 pl-5">
              <li>Protect and expand High Value Champions with premium engagement.</li>
              <li>Convert Data Heavy users to higher-margin unlimited bundles.</li>
              <li>Lift budget users with targeted postpaid migration paths.</li>
            </ul>
          </div>
          <div>
            <p className="font-semibold text-red-700">Risk Mitigation Priorities</p>
            <ul className="mt-1 list-disc space-y-1 pl-5">
              <li>Prioritize At Risk Detractors through rapid complaint resolution.</li>
              <li>Create save campaigns for short-tenure users.</li>
              <li>Track churn-warning signals weekly by segment.</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  )
}