import { platformMetrics, reportSections, segments } from './mockData'

type ExportOptions = {
  ids: boolean
  labels: boolean
  metrics: boolean
  visuals: boolean
  strategy: boolean
  appendix: boolean
}

function downloadTextFile(fileName: string, content: string, mimeType = 'text/plain;charset=utf-8') {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = fileName
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}

function csvEscape(value: string | number | boolean) {
  const text = String(value)
  if (text.includes(',') || text.includes('"') || text.includes('\n')) {
    return `"${text.replace(/"/g, '""')}"`
  }
  return text
}

function buildSegmentCsv() {
  const headers = ['segment', 'customers', 'market_share_pct', 'arpu', 'data_usage_gb', 'voice_minutes', 'tenure_years', 'churn_risk_label', 'churn_risk_pct']
  const rows = segments.map((segment) => [
    segment.name,
    segment.customers,
    segment.share,
    segment.arpu,
    segment.dataUsage,
    segment.voiceMinutes,
    segment.tenure,
    segment.churnRiskLabel,
    segment.churnRiskPct
  ])

  return [headers.join(','), ...rows.map((row) => row.map(csvEscape).join(','))].join('\n')
}

function buildSqlDump() {
  const insertRows = segments
    .map((segment) => {
      const values = [
        segment.id,
        segment.name,
        segment.customers,
        segment.share,
        segment.arpu,
        segment.dataUsage,
        segment.voiceMinutes,
        segment.tenure,
        segment.churnRiskLabel,
        segment.churnRiskPct
      ]
      const serialized = values
        .map((value) => (typeof value === 'string' ? `'${value.replace(/'/g, "''")}'` : value))
        .join(', ')
      return `(${serialized})`
    })
    .join(',\n')

  return `CREATE TABLE IF NOT EXISTS smartseg_segments (
  id TEXT,
  name TEXT,
  customers INTEGER,
  share REAL,
  arpu REAL,
  data_usage REAL,
  voice_minutes REAL,
  tenure REAL,
  churn_risk_label TEXT,
  churn_risk_pct INTEGER
);

INSERT INTO smartseg_segments (id, name, customers, share, arpu, data_usage, voice_minutes, tenure, churn_risk_label, churn_risk_pct)
VALUES
${insertRows};`
}

function buildSummaryText(options?: ExportOptions) {
  const lines = [
    'SmartSeg Customer Segmentation Report',
    `Generated: ${new Date().toLocaleString()}`,
    '',
    `Total Customers: ${platformMetrics.totalCustomers.toLocaleString()}`,
    `Optimal Clusters: ${platformMetrics.optimalClusters}`,
    `Model Accuracy: ${platformMetrics.modelAccuracy}%`,
    `Silhouette Score: ${platformMetrics.silhouetteScore}`,
    '',
    'Segments:'
  ]

  for (const segment of segments) {
    lines.push(`- ${segment.name}: ${segment.customers.toLocaleString()} customers | ARPU $${segment.arpu}`)
  }

  lines.push('', 'Report Sections:')
  for (const section of reportSections) {
    lines.push(`- ${section.name} (${section.pages} pages)`) 
  }

  if (options) {
    lines.push('', 'Export Options:')
    lines.push(`- include_ids: ${options.ids}`)
    lines.push(`- include_labels: ${options.labels}`)
    lines.push(`- include_metrics: ${options.metrics}`)
    lines.push(`- include_visuals: ${options.visuals}`)
    lines.push(`- include_strategy: ${options.strategy}`)
    lines.push(`- include_appendix: ${options.appendix}`)
  }

  return lines.join('\n')
}

export function downloadReportPdf() {
  downloadTextFile('Customer_Segmentation_Report.pdf', buildSummaryText(), 'application/pdf')
}

export function downloadPowerPoint() {
  downloadTextFile('Strategic_Insights_Deck.pptx', buildSummaryText(), 'application/vnd.openxmlformats-officedocument.presentationml.presentation')
}

export function downloadExcel() {
  downloadTextFile('Segment_Data_Export.xlsx', buildSegmentCsv(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
}

export function downloadCsv() {
  downloadTextFile('segments.csv', buildSegmentCsv(), 'text/csv;charset=utf-8')
}

export function downloadJson(options?: ExportOptions) {
  const payload = {
    metadata: {
      generated_at: new Date().toISOString(),
      total_customers: platformMetrics.totalCustomers,
      model_accuracy: platformMetrics.modelAccuracy / 100,
      silhouette_score: platformMetrics.silhouetteScore
    },
    export_options: options,
    segments: segments.map((segment) => ({
      id: segment.id,
      name: segment.name,
      customers: segment.customers,
      market_share_pct: segment.share,
      arpu: segment.arpu,
      data_usage_gb: segment.dataUsage,
      voice_minutes: segment.voiceMinutes,
      tenure_years: segment.tenure,
      churn_risk_label: segment.churnRiskLabel,
      churn_risk_pct: segment.churnRiskPct
    }))
  }

  downloadTextFile('segments.json', JSON.stringify(payload, null, 2), 'application/json;charset=utf-8')
}

export function downloadSql() {
  downloadTextFile('segments_dump.sql', buildSqlDump(), 'application/sql;charset=utf-8')
}

export function downloadBatchPackage(options: ExportOptions) {
  const payload = {
    package: 'SmartSeg Complete Export Package',
    generated_at: new Date().toISOString(),
    files: [
      'Customer_Segmentation_Report.pdf',
      'Strategic_Insights_Deck.pptx',
      'Segment_Data_Export.xlsx',
      'segments.json',
      'segments.csv',
      'segments_dump.sql'
    ],
    options
  }

  downloadTextFile('smartseg_export_package.zip.txt', JSON.stringify(payload, null, 2), 'text/plain;charset=utf-8')
}

export function openEmailDraft() {
  const subject = encodeURIComponent('SmartSeg Customer Segmentation Report')
  const body = encodeURIComponent('Please find the attached SmartSeg segmentation report package.\n\nRegards,\nMarketing Analytics')
  window.location.href = `mailto:?subject=${subject}&body=${body}`
}

export function printPreview() {
  window.print()
}
