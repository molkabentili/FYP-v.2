import { Download } from 'lucide-react'
import { useState } from 'react'
import { Button } from '../components/ui/Button'
import { Card, CardTitle } from '../components/ui/Card'
import { Switch } from '../components/ui/Switch'
import {
  downloadBatchPackage,
  downloadCsv,
  downloadExcel,
  downloadJson,
  downloadPowerPoint,
  downloadReportPdf,
  downloadSql
} from '../data/exporters'

const formats = [
  ['PDF Report', '~8 MB'],
  ['Excel Workbook', '~3 MB'],
  ['PowerPoint Deck', '~12 MB'],
  ['JSON API', '~500 KB'],
  ['CSV Data', '~2 MB'],
  ['SQL Dump', '~1 MB']
]

export function ExportPage() {
  const [options, setOptions] = useState({
    ids: true,
    labels: true,
    metrics: true,
    visuals: true,
    strategy: true,
    appendix: false
  })

  const handleFormatDownload = (name: string) => {
    if (name === 'PDF Report') {
      downloadReportPdf()
      return
    }
    if (name === 'Excel Workbook') {
      downloadExcel()
      return
    }
    if (name === 'PowerPoint Deck') {
      downloadPowerPoint()
      return
    }
    if (name === 'JSON API') {
      downloadJson(options)
      return
    }
    if (name === 'CSV Data') {
      downloadCsv()
      return
    }
    if (name === 'SQL Dump') {
      downloadSql()
      return
    }
  }

  return (
    <div className="container-page space-y-6">
      <h2 className="text-2xl font-bold">Export Center</h2>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {formats.map(([name, size]) => (
          <Card key={name}>
            <CardTitle className="text-base">{name}</CardTitle>
            <p className="text-sm text-slate-600">Estimated size: {size}</p>
            <Button className="mt-3 w-full" onClick={() => handleFormatDownload(name)}><Download size={16} className="mr-2 inline" />Download</Button>
          </Card>
        ))}
      </div>

      <Card>
        <CardTitle>Export Configuration</CardTitle>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {[
            ['Include Customer IDs', 'ids'],
            ['Include Segment Labels', 'labels'],
            ['Include Cluster Metrics', 'metrics'],
            ['Include Visualizations', 'visuals'],
            ['Include Business Strategies', 'strategy'],
            ['Include Technical Appendix', 'appendix']
          ].map(([label, key]) => (
            <div key={label} className="flex items-center justify-between rounded-lg bg-gray-50 p-3 text-sm">
              <span>{label}</span>
              <Switch checked={options[key as keyof typeof options]} onCheckedChange={(value) => setOptions((prev) => ({ ...prev, [key]: value }))} />
            </div>
          ))}
        </div>
      </Card>

      <Card className="border-2 border-[var(--ooredoo-red)]">
        <CardTitle>Batch Export</CardTitle>
        <p className="mt-1 text-sm text-slate-600">Complete package with all 6 formats, ZIP archive ~27 MB.</p>
        <Button className="mt-3" onClick={() => downloadBatchPackage(options)}>Download Complete Package</Button>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle>API Integration</CardTitle>
          <div className="mt-3 rounded-lg bg-gray-900 p-4 text-xs text-gray-100">GET https://api.smartseg.ooredoo.com/v1/segments\nAuth: API Key Required\nRate Limit: 1000 req/hour\nFormat: JSON</div>
          <pre className="mt-3 overflow-x-auto rounded-lg bg-gray-100 p-3 text-xs">{`{
  "segments": [{"name": "High Value Customers", "customers": 2847}],
  "metadata": {"model_accuracy": 0.87, "generated_at": "2026-02-27"}
}`}</pre>
        </Card>

        <Card>
          <CardTitle>Export History</CardTitle>
          <ul className="mt-3 space-y-2 text-sm">
            <li className="rounded-lg bg-gray-50 p-3 flex justify-between"><span>Customer_Segmentation_Report.pdf</span><Button variant="ghost" onClick={downloadReportPdf}>Re-download</Button></li>
            <li className="rounded-lg bg-gray-50 p-3 flex justify-between"><span>Segment_Data_Export.xlsx</span><Button variant="ghost" onClick={downloadExcel}>Re-download</Button></li>
            <li className="rounded-lg bg-gray-50 p-3 flex justify-between"><span>Strategic_Insights_Deck.pptx</span><Button variant="ghost" onClick={downloadPowerPoint}>Re-download</Button></li>
          </ul>
        </Card>
      </div>
    </div>
  )
}
