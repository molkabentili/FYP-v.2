import { AlertTriangle, CheckCircle2, Download, Mail, Printer } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Card, CardTitle } from '../components/ui/Card'
import { formatAtRiskChurn, getDisplaySegments, shouldShowChurnRisk } from '../../services/segmentTransform'
import {
  downloadExcel,
  downloadPowerPoint,
  downloadReportPdf,
  openEmailDraft,
  printPreview
} from '../data/exporters'

function readClusteringResults() {
  try {
    const stored = sessionStorage.getItem('smartseg_clustering_results')
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

function formatNumber(value: unknown, digits = 3) {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : 'N/A'
}

export function ReportPage() {
  const reportSegments = getDisplaySegments()
  const clusteringResults = readClusteringResults()
  const metrics = clusteringResults?.metrics ?? {}
  const silhouetteScore = metrics.silhouette_score ?? metrics.silhouette ?? null
  const modelAccuracy = typeof silhouetteScore === 'number'
    ? Math.max(0, Math.min(100, Math.round(((silhouetteScore + 1) / 2) * 100)))
    : null
  const totalCustomers = reportSegments.reduce((sum, segment) => sum + segment.customers, 0)
  const warningCount = reportSegments.reduce((sum, segment) => sum + segment.validationWarnings.length, 0)

  return (
    <div className="container-page grid gap-4 lg:grid-cols-3">
      <div className="space-y-4 lg:col-span-2">
        <Card className="overflow-hidden p-0">
          <div className="brand-gradient p-5 text-white">
            <h2 className="text-xl font-bold">SmartSeg Customer Segmentation Report</h2>
            <div className="mt-3 grid grid-cols-3 gap-2 text-center text-sm">
              <div><p className="font-bold">{totalCustomers.toLocaleString()}</p><p className="text-red-100">Customers</p></div>
              <div><p className="font-bold">{reportSegments.length}</p><p className="text-red-100">Business Segments</p></div>
              <div><p className="font-bold">{modelAccuracy === null ? 'N/A' : `${modelAccuracy}%`}</p><p className="text-red-100">Accuracy</p></div>
            </div>
          </div>
          <div className="p-5">
            <CardTitle className="text-base">Run Summary</CardTitle>
            <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
              <p>Generated: {new Date().toLocaleString()}</p>
              <p>Backend clusters: {clusteringResults?.n_clusters ?? 'N/A'}</p>
              <p>Silhouette score: {formatNumber(silhouetteScore)}</p>
              <p>Davies-Bouldin: {formatNumber(metrics.davies_bouldin_score ?? metrics.davies_bouldin_index ?? metrics.davies_bouldin)}</p>
              <p>Calinski-Harabasz: {formatNumber(metrics.calinski_harabasz_score ?? metrics.calinski_harabasz_index ?? metrics.calinski_harabasz, 1)}</p>
              <p>Warnings: {warningCount}</p>
            </div>
          </div>
        </Card>

        <Card>
          <CardTitle>Executive Summary Preview</CardTitle>
          <div className="mt-4 rounded-xl border bg-white p-5">
            <h3 className="text-lg font-bold">Executive Summary</h3>
            <p className="mt-2 text-sm text-slate-700">
              This report summarizes business segments calculated from backend cluster metrics, including customer mix, ARPU in DT/TND, usage, tenure in months, and churn risk for campaign targeting.
              K-Means creates the mathematical clusters first; the business interpretation layer then names and aggregates clusters with the same telecom meaning.
            </p>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-700">
              {reportSegments.map((segment) => (
                <li key={segment.id}>
                  {segment.name}: {segment.customers.toLocaleString()} customers, {segment.share}% share, ARPU {segment.arpu.toFixed(2)} DT/TND, data {segment.dataUsage.toFixed(2)} GB/mo, voice {segment.voiceMinutes.toFixed(0)} min/mo, tenure {segment.tenure.toFixed(1)} months{shouldShowChurnRisk(segment) ? `, At Risk churn ${formatAtRiskChurn(segment)}` : ''}.
                </li>
              ))}
            </ul>
          </div>
        </Card>

        {warningCount > 0 && (
          <Card>
            <CardTitle>Segment Validation Warnings</CardTitle>
            <div className="mt-3 space-y-2 text-sm">
              {reportSegments.flatMap((segment) =>
                segment.validationWarnings.map((warning) => (
                  <p key={`${segment.id}-${warning}`} className="flex gap-2 rounded-md bg-yellow-50 p-2 text-yellow-800">
                    <AlertTriangle size={16} /> {segment.name}: {warning}
                  </p>
                ))
              )}
            </div>
          </Card>
        )}
      </div>

      <div className="space-y-4">
        <Card>
          <CardTitle>Download Options</CardTitle>
          <div className="mt-3 space-y-2">
            <Button className="w-full" onClick={downloadReportPdf}>PDF Report</Button>
            <Button variant="secondary" className="w-full" onClick={downloadPowerPoint}>PowerPoint Deck</Button>
            <Button variant="secondary" className="w-full" onClick={downloadExcel}>Excel Data</Button>
            <Button variant="secondary" className="w-full" onClick={openEmailDraft}><Mail size={16} className="mr-2 inline" />Email Report</Button>
            <Button variant="secondary" className="w-full" onClick={printPreview}><Printer size={16} className="mr-2 inline" />Print Preview</Button>
          </div>
        </Card>

        <Card>
          <CardTitle>Quick Stats</CardTitle>
          <ul className="mt-2 space-y-1 text-sm">
            {reportSegments.map((segment) => (
              <li key={segment.id} className="flex items-center justify-between gap-3">
                <span>{segment.name}</span>
                <span>{segment.customers.toLocaleString()}</span>
              </li>
            ))}
          </ul>
          <div className="mt-3 flex items-center gap-2 rounded-md bg-gray-50 p-2 text-sm text-slate-700">
            <CheckCircle2 size={16} /> Values use current backend result data.
          </div>
          <Button variant="ghost" className="mt-3 w-full" onClick={downloadReportPdf}><Download size={16} className="mr-2 inline" />Download Latest Pack</Button>
        </Card>
      </div>
    </div>
  )
}
