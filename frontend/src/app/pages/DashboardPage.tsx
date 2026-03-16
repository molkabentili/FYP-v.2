import { AlertTriangle, DollarSign, TrendingUp, Users } from 'lucide-react'
import { ReactNode } from 'react'
import { Card, CardTitle } from '../components/ui/Card'
import { segments, trendData } from '../data/mockData'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

export function DashboardPage() {
  const revenueBySegment = segments.map((segment) => ({ name: segment.name, revenue: Number(((segment.customers * segment.arpu) / 1000).toFixed(1)), color: segment.color }))

  return (
    <div className="space-y-4 pt-4">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard icon={<DollarSign size={18} />} title="Total Revenue" value="$1,248K" delta="+5.8%" tone="green" />
        <MetricCard icon={<Users size={18} />} title="Total Customers" value="15,400" delta="+0.3%" tone="blue" />
        <MetricCard icon={<TrendingUp size={18} />} title="Average ARPU" value="$81.05" delta="+3.2%" tone="purple" />
        <MetricCard icon={<AlertTriangle size={18} />} title="Churn Rate" value="24.8%" delta="+0.6%" tone="red" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle>Revenue Trend</CardTitle>
          <div className="mt-4 h-64"><ResponsiveContainer width="100%" height="100%"><LineChart data={trendData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="month" /><YAxis /><Tooltip /><Line type="monotone" dataKey="revenue" stroke="#22c55e" strokeWidth={2} /></LineChart></ResponsiveContainer></div>
        </Card>
        <Card>
          <CardTitle>Customer Growth</CardTitle>
          <div className="mt-4 h-64"><ResponsiveContainer width="100%" height="100%"><LineChart data={trendData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="month" /><YAxis /><Tooltip /><Line type="monotone" dataKey="customers" stroke="#3b82f6" strokeWidth={2} /></LineChart></ResponsiveContainer></div>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle>Customer Distribution</CardTitle>
          <div className="mt-4 h-72"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={segments} dataKey="share" nameKey="name" outerRadius={110} label>{segments.map((segment) => <Cell key={segment.id} fill={segment.color} />)}</Pie><Tooltip /><Legend /></PieChart></ResponsiveContainer></div>
        </Card>
        <Card>
          <CardTitle>Revenue by Segment</CardTitle>
          <div className="mt-4 h-72"><ResponsiveContainer width="100%" height="100%"><BarChart data={revenueBySegment}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" hide /><YAxis /><Tooltip /><Bar dataKey="revenue">{revenueBySegment.map((entry) => <Cell key={entry.name} fill={entry.color} />)}</Bar></BarChart></ResponsiveContainer></div>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle>ARPU by Segment</CardTitle>
          <div className="mt-4 h-64"><ResponsiveContainer width="100%" height="100%"><BarChart data={segments} layout="vertical"><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" /><YAxis type="category" dataKey="name" width={130} /><Tooltip /><Bar dataKey="arpu">{segments.map((segment) => <Cell key={segment.id} fill={segment.color} />)}</Bar></BarChart></ResponsiveContainer></div>
        </Card>
        <Card>
          <CardTitle>Churn Risk by Segment</CardTitle>
          <div className="mt-4 h-64"><ResponsiveContainer width="100%" height="100%"><BarChart data={segments}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" hide /><YAxis /><Tooltip /><Bar dataKey="churnRiskPct">{segments.map((segment) => <Cell key={segment.id} fill={segment.color} />)}</Bar></BarChart></ResponsiveContainer></div>
        </Card>
      </div>

      <Card>
        <CardTitle>Key Dashboard Insights</CardTitle>
        <div className="mt-3 grid gap-3 md:grid-cols-3 text-sm">
          <div className="rounded-lg bg-green-50 p-3"><p className="font-semibold text-green-700">Positive Trend</p><p>High Value Champions show steady growth and strong retention performance.</p></div>
          <div className="rounded-lg bg-blue-50 p-3"><p className="font-semibold text-blue-700">Growth Opportunity</p><p>Data Heavy Streamers remain the top upsell channel for 5G bundles.</p></div>
          <div className="rounded-lg bg-red-50 p-3"><p className="font-semibold text-red-700">Immediate Action Required</p><p>At Risk Detractors need targeted save offers and complaint resolution.</p></div>
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