import { BarChart3, CheckCircle2, CircleDashed, Database, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Card, CardDescription, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { platformMetrics } from '../data/mockData'

const steps = [
  { title: 'Upload Customer Data', color: 'bg-blue-500' },
  { title: 'Run ML Segmentation', color: 'bg-green-500' },
  { title: 'Analyze Segments', color: 'bg-purple-500' },
  { title: 'Strategic Insights', color: 'bg-orange-500' }
]

export function HomePage() {
  return (
    <div className="container-page space-y-6">
      <section className="brand-gradient relative overflow-hidden rounded-2xl p-8 text-white">
        <div className="absolute right-6 top-6 opacity-20"><BarChart3 size={96} /></div>
        <h2 className="text-3xl font-bold">SmartSeg Platform</h2>
        <p className="mt-2 max-w-2xl text-sm text-red-100">A decision-support customer segmentation platform tailored for telecom marketing teams.</p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link to="/upload"><Button className="bg-white text-[var(--ooredoo-red)] hover:bg-red-50">Get Started</Button></Link>
          <Link to="/results"><Button variant="secondary">View Demo Results</Button></Link>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {steps.map((step, index) => (
          <Card key={step.title}>
            <div className="mb-3 flex items-center justify-between">
              <span className="badge-brand">Step {index + 1}</span>
              <span className={`h-3 w-3 rounded-full ${step.color}`} />
            </div>
            <CardTitle className="text-base">{step.title}</CardTitle>
          </Card>
        ))}
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Card className="brand-subtle">
          <CardTitle>Why SmartSeg?</CardTitle>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {['Data-driven customer targeting', 'Reduced churn via proactive actions', 'Higher ARPU through upsell precision', 'Actionable segment-level strategies', 'Defense-ready reporting outputs'].map((item) => (
              <li key={item} className="flex items-center gap-2"><CheckCircle2 size={16} className="text-green-600" />{item}</li>
            ))}
          </ul>
        </Card>
        <Card>
          <CardTitle>Current Demo Dataset</CardTitle>
          <div className="mt-3 grid grid-cols-3 gap-3 text-center">
            <div><p className="text-xl font-bold text-[var(--ooredoo-red)]">{platformMetrics.totalCustomers.toLocaleString()}</p><p className="text-xs text-slate-600">Customers</p></div>
            <div><p className="text-xl font-bold text-[var(--ooredoo-red)]">{platformMetrics.optimalClusters}</p><p className="text-xs text-slate-600">Clusters</p></div>
            <div><p className="text-xl font-bold text-[var(--ooredoo-red)]">{platformMetrics.modelAccuracy}%</p><p className="text-xs text-slate-600">Accuracy</p></div>
          </div>
        </Card>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardTitle className="mb-2">Supported Algorithms</CardTitle>
          <CardDescription>K-Means, Hierarchical, DBSCAN, GMM</CardDescription>
        </Card>
        <Card>
          <CardTitle className="mb-2">Data Requirements</CardTitle>
          <CardDescription>CSV format, minimum records, required telecom features</CardDescription>
        </Card>
        <Card>
          <CardTitle className="mb-2">Export Formats</CardTitle>
          <CardDescription>PDF, Excel, JSON, CSV</CardDescription>
        </Card>
      </section>

      <section className="card brand-subtle">
        <h3 className="text-lg font-semibold">Quick Start Guide</h3>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <div className="rounded-lg bg-white p-3"><p className="badge-brand">1</p><p className="mt-2 text-sm">Load demo dataset from Upload page.</p></div>
          <div className="rounded-lg bg-white p-3"><p className="badge-brand">2</p><p className="mt-2 text-sm">Configure K-Means parameters.</p></div>
          <div className="rounded-lg bg-white p-3"><p className="badge-brand">3</p><p className="mt-2 text-sm">Review insights and export strategy report.</p></div>
        </div>
        <div className="mt-4 flex items-center gap-2 text-sm text-slate-700"><Sparkles size={16} /> Optimized for telecom segmentation workflows.</div>
        <div className="mt-1 flex items-center gap-2 text-sm text-slate-700"><Database size={16} /> UTF-8 CSV files recommended for best compatibility.</div>
        <div className="mt-1 flex items-center gap-2 text-sm text-slate-700"><CircleDashed size={16} /> End-to-end demo flow available without backend connection.</div>
      </section>
    </div>
  )
}