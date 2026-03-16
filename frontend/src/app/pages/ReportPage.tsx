import { CheckCircle2, Download, Mail, Printer, XCircle } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Card, CardTitle } from '../components/ui/Card'
import { reportSections, segments } from '../data/mockData'
import {
  downloadExcel,
  downloadPowerPoint,
  downloadReportPdf,
  openEmailDraft,
  printPreview
} from '../data/exporters'

export function ReportPage() {
  return (
    <div className="container-page grid gap-4 lg:grid-cols-3">
      <div className="space-y-4 lg:col-span-2">
        <Card className="overflow-hidden p-0">
          <div className="brand-gradient p-5 text-white">
            <h2 className="text-xl font-bold">Customer Segmentation Analysis Report</h2>
            <div className="mt-3 grid grid-cols-3 gap-2 text-center text-sm">
              <div><p className="font-bold">15,400</p><p className="text-red-100">Customers</p></div>
              <div><p className="font-bold">4</p><p className="text-red-100">Segments</p></div>
              <div><p className="font-bold">87%</p><p className="text-red-100">Accuracy</p></div>
            </div>
          </div>
          <div className="p-5">
            <CardTitle className="text-base">Report Contents</CardTitle>
            <ul className="mt-3 space-y-2 text-sm">
              {reportSections.map((section) => (
                <li key={section.name} className="flex items-center justify-between rounded-md bg-gray-50 px-3 py-2">
                  <span>{section.name} ({section.pages} pages)</span>
                  {section.ready ? <CheckCircle2 size={16} className="text-green-600" /> : <XCircle size={16} className="text-red-500" />}
                </li>
              ))}
            </ul>
            <div className="mt-4 rounded-lg bg-gray-900 p-3 text-sm text-gray-100">
              <p>Total pages: 37</p>
              <p>Generated: February 27, 2026</p>
              <p>Formats: PDF, PPTX, XLSX</p>
            </div>
          </div>
        </Card>

        <Card>
          <CardTitle>Executive Summary Preview</CardTitle>
          <div className="mt-4 rounded-xl border bg-white p-5">
            <h3 className="text-lg font-bold">Executive Summary</h3>
            <p className="mt-2 text-sm text-slate-700">This analysis identifies four telecom customer segments with distinct revenue, usage, and churn characteristics, enabling targeted retention, upselling, and campaign strategies with measurable business impact.</p>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-700">
              <li>High Value Champions deliver premium ARPU with strong loyalty.</li>
              <li>Data Heavy Streamers represent the largest upsell opportunity.</li>
              <li>Budget Conscious customers require value-driven migration paths.</li>
              <li>At Risk Detractors need immediate save and recovery actions.</li>
            </ul>
          </div>
        </Card>
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
            {segments.map((segment) => <li key={segment.id} className="flex items-center justify-between"><span>{segment.name}</span><span>{segment.customers.toLocaleString()}</span></li>)}
          </ul>
          <Button variant="ghost" className="mt-3 w-full" onClick={downloadReportPdf}><Download size={16} className="mr-2 inline" />Download Latest Pack</Button>
        </Card>
      </div>
    </div>
  )
}