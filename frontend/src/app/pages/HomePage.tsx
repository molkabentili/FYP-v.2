import { BarChart3, CheckCircle2, Database, Download, FileText, Sparkles, Target, Upload } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Card, CardDescription, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'

const steps = [
  {
    title: 'Upload Customer Data',
    description: 'Import a CSV containing customer, revenue, usage, tenure, satisfaction, payment, and churn-related fields.',
    color: 'bg-blue-500'
  },
  {
    title: 'Configure Segmentation',
    description: 'Choose K-Means settings and cluster count based on the level of business granularity needed.',
    color: 'bg-green-500'
  },
  {
    title: 'Map Business Segments',
    description: 'Convert model clusters into business-ready groups such as Premium, High Value, Medium Value, Low Value, and At Risk.',
    color: 'bg-purple-500'
  },
  {
    title: 'Activate Campaigns',
    description: 'Review dashboards, export targeted customers, and use the report for retention, upsell, and campaign planning.',
    color: 'bg-orange-500'
  }
]

const capabilities = [
  'Transforms raw telecom customer data into actionable business segments',
  'Calculates segment-level averages for ARPU, usage, tenure, and churn risk',
  'Highlights revenue opportunities and retention priorities',
  'Exports customer contact lists by business segment for campaign execution',
  'Generates reporting outputs for marketing and decision-support workflows'
]

export function HomePage() {
  return (
    <div className="container-page space-y-6">
      <section className="brand-gradient relative overflow-hidden rounded-2xl p-8 text-white">
        <div className="absolute right-6 top-6 opacity-20"><BarChart3 size={96} /></div>
        <h2 className="text-3xl font-bold">SmartSeg Platform</h2>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-red-100">
          SmartSeg is a telecom customer intelligence platform that turns customer usage, revenue, tenure, satisfaction, payment, and churn signals into practical business segments for marketing action. It helps analysts move from raw data to targeted campaigns, segment dashboards, and decision-ready reports.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link to="/upload"><Button className="bg-white text-[var(--ooredoo-red)] hover:bg-red-50">Upload Customer Data</Button></Link>
          <Link to="/configure"><Button variant="secondary">Run Segmentation</Button></Link>
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
            <CardDescription className="mt-2">{step.description}</CardDescription>
          </Card>
        ))}
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Card className="brand-subtle">
          <CardTitle>What SmartSeg Does</CardTitle>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {capabilities.map((item) => (
              <li key={item} className="flex items-center gap-2"><CheckCircle2 size={16} className="text-green-600" />{item}</li>
            ))}
          </ul>
        </Card>
        <Card>
          <CardTitle>Business Outputs</CardTitle>
          <div className="mt-3 grid gap-3 text-sm text-slate-700 sm:grid-cols-2">
            <div className="rounded-lg bg-gray-50 p-3"><Target size={18} className="mb-2 text-[var(--ooredoo-red)]" /> Business segment cards</div>
            <div className="rounded-lg bg-gray-50 p-3"><BarChart3 size={18} className="mb-2 text-[var(--ooredoo-red)]" /> Dashboard charts</div>
            <div className="rounded-lg bg-gray-50 p-3"><Download size={18} className="mb-2 text-[var(--ooredoo-red)]" /> Targeted exports</div>
            <div className="rounded-lg bg-gray-50 p-3"><FileText size={18} className="mb-2 text-[var(--ooredoo-red)]" /> Strategy reports</div>
          </div>
        </Card>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardTitle className="mb-2">Input Data</CardTitle>
          <CardDescription>CSV customer data with telecom metrics such as ARPU, data usage, voice usage, tenure, satisfaction, complaints, late payments, activity, and churn probability.</CardDescription>
        </Card>
        <Card>
          <CardTitle className="mb-2">Segmentation Logic</CardTitle>
          <CardDescription>K-Means clustering groups customers by similar behavior, then SmartSeg maps those clusters into business segment names for marketing interpretation.</CardDescription>
        </Card>
        <Card>
          <CardTitle className="mb-2">Export Formats</CardTitle>
          <CardDescription>Export all customers or a selected business segment as CSV or Excel for contact targeting and campaign activation.</CardDescription>
        </Card>
      </section>

      <section className="card brand-subtle">
        <h3 className="text-lg font-semibold">Workflow</h3>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <div className="rounded-lg bg-white p-3"><p className="badge-brand">1</p><p className="mt-2 text-sm">Upload and preprocess customer data so the model can use clean numerical features.</p></div>
          <div className="rounded-lg bg-white p-3"><p className="badge-brand">2</p><p className="mt-2 text-sm">Run K-Means with the selected cluster count and review backend validation metrics.</p></div>
          <div className="rounded-lg bg-white p-3"><p className="badge-brand">3</p><p className="mt-2 text-sm">Analyze business segments, export targeted customers, and generate reporting outputs.</p></div>
        </div>
        <div className="mt-4 flex items-center gap-2 text-sm text-slate-700"><Sparkles size={16} /> Optimized for telecom segmentation workflows.</div>
        <div className="mt-1 flex items-center gap-2 text-sm text-slate-700"><Database size={16} /> UTF-8 CSV files recommended for best compatibility.</div>
        <div className="mt-1 flex items-center gap-2 text-sm text-slate-700"><Upload size={16} /> Start with Upload Data, then Run Segmentation, View Results, and Export customer lists.</div>
      </section>
    </div>
  )
}
