import { AlertTriangle, Coins, Download, Mail, TrendingUp, Users } from 'lucide-react'
import { ReactNode } from 'react'
import { Card, CardTitle } from '../components/ui/Card'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { formatAtRiskChurn, getDisplaySegments, DisplaySegment } from '../../services/segmentTransform'
import { Button } from '../components/ui/Button'
import { downloadTargetedCustomersCsv, downloadTargetedCustomersExcel, emailTargetedCustomersCsv } from '../data/exporters'

export function DashboardPage() {
  const dynamicSegments = getDisplaySegments()
  const activeSegments: DisplaySegment[] = dynamicSegments
  const revenueBySegment = activeSegments.map((segment) => ({ name: segment.name, revenue: Number(((segment.customers * segment.arpu) / 1000).toFixed(1)), color: segment.color }))
  const totalCustomers = activeSegments.reduce((sum, segment) => sum + segment.customers, 0)
  const totalRevenue = activeSegments.reduce((sum, segment) => sum + (segment.customers * segment.arpu), 0)
  const avgArpu = totalCustomers > 0 ? totalRevenue / totalCustomers : 0
  const atRiskSegment = activeSegments.find((segment) => segment.showChurnRisk)
  const atRiskChurn = atRiskSegment ? formatAtRiskChurn(atRiskSegment) : 'N/A'
  const churnChartData = atRiskSegment ? [atRiskSegment] : []
  const highestRevenueSegment = [...activeSegments].sort((a, b) => b.customers * b.arpu - a.customers * a.arpu)[0]

  if (activeSegments.length === 0) {
    return (
      <div className="space-y-4 pt-4">
        <Card>
          <CardTitle>No Segmentation Results</CardTitle>
          <p className="mt-2 text-sm text-slate-600">Run segmentation to populate business-segment dashboard metrics.</p>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-4 pt-4">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard icon={<Coins size={18} />} title="Total Revenue" value={`${(totalRevenue / 1000).toFixed(1)}K DT/TND`} delta="Calculated from current segments" tone="green" />
        <MetricCard icon={<Users size={18} />} title="Total Customers" value={totalCustomers.toLocaleString()} delta="Live run" tone="blue" />
        <MetricCard icon={<TrendingUp size={18} />} title="Average ARPU" value={`${avgArpu.toFixed(2)} DT/TND`} delta="Weighted by customers" tone="purple" />
        <MetricCard icon={<AlertTriangle size={18} />} title="At Risk Churn" value={atRiskChurn} delta="At Risk segment only" tone="red" />
      </div>

      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base">Business Segment Exports</CardTitle>
            <p className="text-sm text-slate-600">Export all customers or download a selected business segment from the cards below.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => void downloadTargetedCustomersCsv()}><Download size={14} className="mr-1 inline" />Export All Customers</Button>
            <Button variant="secondary" onClick={() => void emailTargetedCustomersCsv()}><Mail size={14} className="mr-1 inline" />Email CSV</Button>
            <Button variant="secondary" onClick={() => void downloadTargetedCustomersExcel()}>Export All Excel</Button>
          </div>
        </div>
      </Card>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {activeSegments.map((segment) => (
          <Card key={segment.id} className="border-t-4" style={{ borderTopColor: segment.color }}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <CardTitle className="text-base">{segment.name}</CardTitle>
                <p className="text-sm text-slate-600">{segment.customers.toLocaleString()} customers ({segment.share.toFixed(2)}%)</p>
                <p className="mt-1 text-xs text-slate-500">Source clusters: {segment.sourceClusterIds.join(', ') || 'N/A'}</p>
              </div>
              {segment.showChurnRisk && (
                <span className="rounded-md bg-red-50 px-2 py-1 text-xs font-semibold text-red-700">{formatAtRiskChurn(segment)} churn</span>
              )}
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
              <p><span className="text-slate-500">ARPU</span><br /><strong>{segment.arpu.toFixed(2)} DT/TND</strong></p>
              <p><span className="text-slate-500">Data</span><br /><strong>{segment.dataUsage.toFixed(2)}</strong></p>
              <p><span className="text-slate-500">Voice</span><br /><strong>{segment.voiceMinutes.toFixed(0)} min</strong></p>
              <p><span className="text-slate-500">International</span><br /><strong>{segment.internationalMinutes.toFixed(0)} min</strong></p>
              <p><span className="text-slate-500">Tenure</span><br /><strong>{segment.tenure.toFixed(1)} months</strong></p>
              <p><span className="text-slate-500">Satisfaction</span><br /><strong>{segment.satisfaction.toFixed(1)}</strong></p>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Button variant="ghost" onClick={() => void downloadTargetedCustomersCsv({ segment: segment.valueSegmentName })}><Download size={14} className="mr-1 inline" />CSV</Button>
              <Button variant="ghost" onClick={() => void emailTargetedCustomersCsv({ segment: segment.valueSegmentName })}><Mail size={14} className="mr-1 inline" />Email CSV</Button>
              <Button variant="ghost" onClick={() => void downloadTargetedCustomersExcel({ segment: segment.valueSegmentName })}>Excel</Button>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle>Customer Distribution</CardTitle>
          <div className="mt-4 h-72"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={activeSegments} dataKey="share" nameKey="name" outerRadius={110} label>{activeSegments.map((segment) => <Cell key={segment.id} fill={segment.color} />)}</Pie><Tooltip /><Legend /></PieChart></ResponsiveContainer></div>
        </Card>
        <Card>
          <CardTitle>Revenue by Segment</CardTitle>
          <div className="mt-4 h-72"><ResponsiveContainer width="100%" height="100%"><BarChart data={revenueBySegment}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" hide /><YAxis /><Tooltip /><Bar dataKey="revenue">{revenueBySegment.map((entry) => <Cell key={entry.name} fill={entry.color} />)}</Bar></BarChart></ResponsiveContainer></div>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle>ARPU by Segment</CardTitle>
          <div className="mt-4 h-64"><ResponsiveContainer width="100%" height="100%"><BarChart data={activeSegments} layout="vertical"><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" /><YAxis type="category" dataKey="name" width={130} /><Tooltip /><Bar dataKey="arpu">{activeSegments.map((segment) => <Cell key={segment.id} fill={segment.color} />)}</Bar></BarChart></ResponsiveContainer></div>
        </Card>
        <Card>
          <CardTitle>At Risk Churn Percentage</CardTitle>
          {churnChartData.length > 0 ? (
            <div className="mt-4 h-64"><ResponsiveContainer width="100%" height="100%"><BarChart data={churnChartData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" hide /><YAxis /><Tooltip /><Bar dataKey="churnRiskPct">{churnChartData.map((segment) => <Cell key={segment.id} fill={segment.color} />)}</Bar></BarChart></ResponsiveContainer></div>
          ) : (
            <p className="mt-4 text-sm text-slate-600">No At Risk segment is present in this clustering result.</p>
          )}
        </Card>
      </div>

      <Card>
        <CardTitle>Key Dashboard Insights</CardTitle>
        <div className="mt-3 grid gap-3 md:grid-cols-3 text-sm">
          <div className="rounded-lg bg-green-50 p-3"><p className="font-semibold text-green-700">Revenue Concentration</p><p>{highestRevenueSegment?.name ?? 'N/A'} contributes the highest estimated revenue at {highestRevenueSegment ? ((highestRevenueSegment.customers * highestRevenueSegment.arpu) / 1000).toFixed(1) : '0.0'}K DT/TND.</p></div>
          <div className="rounded-lg bg-blue-50 p-3"><p className="font-semibold text-blue-700">Segment Mix</p><p>{activeSegments.length} business segments are available, based on current backend cluster metrics.</p></div>
          <div className="rounded-lg bg-red-50 p-3"><p className="font-semibold text-red-700">Retention Priority</p><p>{atRiskSegment ? `At Risk Customers churn percentage is ${formatAtRiskChurn(atRiskSegment)}.` : 'No At Risk segment is present in this clustering result.'}</p></div>
        </div>
      </Card>
    </div>
  )
}

function MetricCard({ icon, title, value, delta, tone }: { icon: ReactNode; title: string; value: string; delta: string; tone: 'green' | 'blue' | 'purple' | 'red' }) {
  const toneClass = tone === 'green' ? 'text-green-700 bg-green-50' : tone === 'blue' ? 'text-blue-700 bg-blue-50' : tone === 'purple' ? 'text-purple-700 bg-purple-50' : 'text-red-700 bg-red-50'
  return (
    <Card>
      <div className="flex items-start justify-between"><div><p className="text-xs uppercase text-slate-500">{title}</p><p className="text-2xl font-bold">{value}</p></div><div className={`rounded-lg p-2 ${toneClass}`}>{icon}</div></div>
      <p className={`mt-2 text-sm ${tone === 'red' ? 'text-red-600' : 'text-green-600'}`}>{delta}</p>
    </Card>
  )
}
