import { formatAtRiskChurn, getDisplaySegments, shouldShowChurnRisk, type DisplaySegment } from '../../services/segmentTransform'
import { exportCustomers, type CustomerExportRequest } from '../../services/api'
import { platformMetrics, reportSections, segments as mockSegments } from './mockData'

type ExportOptions = {
  ids: boolean
  labels: boolean
  metrics: boolean
  visuals: boolean
  strategy: boolean
  appendix: boolean
}

type ReportMetrics = {
  totalCustomers: number
  numSegments: number
  modelAccuracy: number
  silhouetteScore: number | null
  daviesBouldinScore: number | null
  calinskiHarabaszScore: number | null
}

type ZipEntry = {
  path: string
  content: string | Uint8Array
}

export type CustomerExportFilters = {
  segment?: string
  region?: string
  city?: string
  churnRisk?: string
  minArpu?: number
  maxArpu?: number
}

const textEncoder = new TextEncoder()

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

function downloadBlobFile(fileName: string, blob: Blob) {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = fileName
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}

function getReportSegments(): DisplaySegment[] {
  const generatedSegments = getDisplaySegments()
  if (generatedSegments.length > 0) {
    return generatedSegments
  }

  return mockSegments.map((segment) => ({
    id: segment.id,
    clusterId: segment.id,
    sourceClusterIds: [],
    name: segment.name,
    valueSegmentName: segment.name,
    segmentDescription: segment.characteristics[0] ?? 'Business segment profile',
    color: segment.color,
    customers: segment.customers,
    arpu: segment.arpu,
    share: segment.share,
    dataUsage: segment.dataUsage,
    voiceMinutes: segment.voiceMinutes,
    tenure: segment.tenure,
    tenureUnit: 'months',
    internationalMinutes: 0,
    complaints: 0,
    satisfaction: 0,
    latePayments: 0,
    clv: 0,
    characteristics: segment.characteristics,
    validationWarnings: [],
    churnRiskPct: segment.churnRiskPct,
    churnRiskLabel: segment.churnRiskLabel,
    showChurnRisk: segment.name === 'At Risk Customers'
  }))
}

function getSegmentationLevelLabel() {
  return 'Customer Segmentation'
}

function exportChurnLabel(segment: { name: string; churnRiskLabel: string }) {
  return shouldShowChurnRisk(segment) ? segment.churnRiskLabel : ''
}

function exportChurnPct(segment: { name: string; churnRiskPct: number }) {
  return shouldShowChurnRisk(segment) ? segment.churnRiskPct : ''
}

function exportChurnSummary(segment: { name: string; churnRiskPct: number; churnRiskLabel: string }) {
  return shouldShowChurnRisk(segment)
    ? ` | At Risk churn ${segment.churnRiskLabel} (${formatAtRiskChurn(segment)})`
    : ''
}

function getReportMetrics(reportSegments = getReportSegments()): ReportMetrics {
  const totalCustomers = reportSegments.reduce((sum, segment) => sum + segment.customers, 0)
  const metrics: ReportMetrics = {
    totalCustomers,
    numSegments: reportSegments.length || platformMetrics.optimalClusters,
    modelAccuracy: platformMetrics.modelAccuracy,
    silhouetteScore: platformMetrics.silhouetteScore,
    daviesBouldinScore: null,
    calinskiHarabaszScore: null
  }

  try {
    const stored = sessionStorage.getItem('smartseg_clustering_results')
    if (!stored) return metrics

    const results = JSON.parse(stored)
    const resultMetrics = results.metrics ?? {}
    const silhouette = resultMetrics.silhouette_score ?? resultMetrics.silhouette ?? null
    const daviesBouldin = resultMetrics.davies_bouldin_score ?? resultMetrics.davies_bouldin_index ?? resultMetrics.davies_bouldin ?? null
    const calinskiHarabasz = resultMetrics.calinski_harabasz_score ?? resultMetrics.calinski_harabasz_index ?? resultMetrics.calinski_harabasz ?? null

    return {
      totalCustomers,
      numSegments: reportSegments.length || results.n_clusters || platformMetrics.optimalClusters,
      modelAccuracy: typeof silhouette === 'number' ? Math.round(((silhouette + 1) / 2) * 100) : metrics.modelAccuracy,
      silhouetteScore: typeof silhouette === 'number' ? silhouette : metrics.silhouetteScore,
      daviesBouldinScore: typeof daviesBouldin === 'number' ? daviesBouldin : null,
      calinskiHarabaszScore: typeof calinskiHarabasz === 'number' ? calinskiHarabasz : null
    }
  } catch {
    return metrics
  }
}

function xmlEscape(value: string | number | boolean | null | undefined) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

function crc32(bytes: Uint8Array) {
  let crc = 0xffffffff

  for (const byte of bytes) {
    crc ^= byte
    for (let bit = 0; bit < 8; bit += 1) {
      crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0)
    }
  }

  return (crc ^ 0xffffffff) >>> 0
}

function writeUint16(target: number[], value: number) {
  target.push(value & 0xff, (value >>> 8) & 0xff)
}

function writeUint32(target: number[], value: number) {
  target.push(value & 0xff, (value >>> 8) & 0xff, (value >>> 16) & 0xff, (value >>> 24) & 0xff)
}

function concatBytes(parts: Uint8Array[]) {
  const totalLength = parts.reduce((sum, part) => sum + part.length, 0)
  const output = new Uint8Array(totalLength)
  let offset = 0

  for (const part of parts) {
    output.set(part, offset)
    offset += part.length
  }

  return output
}

function zipDateParts(date = new Date()) {
  const time = (date.getHours() << 11) | (date.getMinutes() << 5) | Math.floor(date.getSeconds() / 2)
  const dosDate = ((date.getFullYear() - 1980) << 9) | ((date.getMonth() + 1) << 5) | date.getDate()
  return { time, dosDate }
}

function createZipBytes(entries: ZipEntry[]) {
  const localParts: Uint8Array[] = []
  const centralParts: Uint8Array[] = []
  const { time, dosDate } = zipDateParts()
  let offset = 0

  for (const entry of entries) {
    const fileNameBytes = textEncoder.encode(entry.path)
    const contentBytes = typeof entry.content === 'string' ? textEncoder.encode(entry.content) : entry.content
    const checksum = crc32(contentBytes)
    const localHeader: number[] = []

    writeUint32(localHeader, 0x04034b50)
    writeUint16(localHeader, 20)
    writeUint16(localHeader, 0x0800)
    writeUint16(localHeader, 0)
    writeUint16(localHeader, time)
    writeUint16(localHeader, dosDate)
    writeUint32(localHeader, checksum)
    writeUint32(localHeader, contentBytes.length)
    writeUint32(localHeader, contentBytes.length)
    writeUint16(localHeader, fileNameBytes.length)
    writeUint16(localHeader, 0)

    const localRecord = concatBytes([new Uint8Array(localHeader), fileNameBytes, contentBytes])
    localParts.push(localRecord)

    const centralHeader: number[] = []
    writeUint32(centralHeader, 0x02014b50)
    writeUint16(centralHeader, 20)
    writeUint16(centralHeader, 20)
    writeUint16(centralHeader, 0x0800)
    writeUint16(centralHeader, 0)
    writeUint16(centralHeader, time)
    writeUint16(centralHeader, dosDate)
    writeUint32(centralHeader, checksum)
    writeUint32(centralHeader, contentBytes.length)
    writeUint32(centralHeader, contentBytes.length)
    writeUint16(centralHeader, fileNameBytes.length)
    writeUint16(centralHeader, 0)
    writeUint16(centralHeader, 0)
    writeUint16(centralHeader, 0)
    writeUint16(centralHeader, 0)
    writeUint32(centralHeader, 0)
    writeUint32(centralHeader, offset)

    centralParts.push(concatBytes([new Uint8Array(centralHeader), fileNameBytes]))
    offset += localRecord.length
  }

  const centralDirectory = concatBytes(centralParts)
  const endRecord: number[] = []
  writeUint32(endRecord, 0x06054b50)
  writeUint16(endRecord, 0)
  writeUint16(endRecord, 0)
  writeUint16(endRecord, entries.length)
  writeUint16(endRecord, entries.length)
  writeUint32(endRecord, centralDirectory.length)
  writeUint32(endRecord, offset)
  writeUint16(endRecord, 0)

  return concatBytes([...localParts, centralDirectory, new Uint8Array(endRecord)])
}

function createZipBlob(entries: ZipEntry[], mimeType = 'application/zip') {
  return new Blob([createZipBytes(entries)], { type: mimeType })
}

function csvEscape(value: string | number | boolean) {
  const text = String(value)
  if (text.includes(',') || text.includes('"') || text.includes('\n')) {
    return `"${text.replace(/"/g, '""')}"`
  }
  return text
}

function normalizeFilePart(value: string) {
  return value.replace(/[^a-z0-9]+/gi, '_').replace(/^_+|_+$/g, '') || 'customers'
}

function getStoredClusteringResults(): any | null {
  try {
    const stored = sessionStorage.getItem('smartseg_clustering_results')
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

function getSegmentedCsvPath(): string {
  const results = getStoredClusteringResults()
  const segmentedCsv = results?.segmented_csv ?? results?.output_file

  if (!segmentedCsv) {
    throw new Error('No segmented customer file found. Run segmentation before exporting customers.')
  }

  return segmentedCsv
}

function toCustomerExportRequest(filters: CustomerExportFilters, exportFormat: 'csv' | 'excel'): CustomerExportRequest {
  return {
    segmented_csv: getSegmentedCsvPath(),
    export_format: exportFormat,
    segment: filters.segment,
    region: filters.region,
    city: filters.city,
    churn_risk: filters.churnRisk,
    min_arpu: filters.minArpu,
    max_arpu: filters.maxArpu
  }
}

async function downloadTargetedCustomers(filters: CustomerExportFilters, exportFormat: 'csv' | 'excel') {
  try {
    const scope = filters.segment ?? 'All_Customers'
    const blob = await exportCustomers(toCustomerExportRequest(filters, exportFormat))
    const extension = exportFormat === 'excel' ? 'xls' : 'csv'
    downloadBlobFile(`${normalizeFilePart(scope)}_customers.${extension}`, blob)
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Customer export failed'
    window.alert(message)
  }
}

function buildTargetedCustomerRows(filters: CustomerExportFilters = {}) {
  const regions = ['Tunis', 'Sfax', 'Sousse', 'Nabeul', 'Ariana', 'Gabes']
  const cities = ['Tunis', 'Sfax', 'Sousse', 'Hammamet', 'Ariana', 'Gabes']
  const channels = ['SMS', 'Email', 'Call Center', 'WhatsApp']
  const rows: Array<Record<string, string | number>> = []
  const selectedSegments = getReportSegments().filter((segment) => {
    if (filters.segment && segment.valueSegmentName !== filters.segment && segment.name !== filters.segment) return false
    if (filters.churnRisk && exportChurnLabel(segment) !== filters.churnRisk) return false
    if (filters.minArpu !== undefined && segment.arpu < filters.minArpu) return false
    if (filters.maxArpu !== undefined && segment.arpu > filters.maxArpu) return false
    return true
  })

  selectedSegments.forEach((segment, segmentIndex) => {
    const exportCount = Math.max(1, segment.customers)

    for (let index = 0; index < exportCount; index += 1) {
      const rowIndex = rows.length + 1
      const region = regions[(segmentIndex + index) % regions.length]
      const city = cities[(segmentIndex * 2 + index) % cities.length]

      if (filters.region && filters.region !== region) continue
      if (filters.city && filters.city !== city) continue

      rows.push({
        Customer_ID: `CUST-${String(rowIndex).padStart(6, '0')}`,
        Full_Name: `Customer ${rowIndex}`,
        Phone_Number: `+216${String(20000000 + rowIndex).slice(-8)}`,
        Email: `customer${rowIndex}@example.tn`,
        Region: region,
        City: city,
        Business_Segment: segment.valueSegmentName,
        ARPU_TND: Number(segment.arpu.toFixed(2)),
        ARPU_DT: Number(segment.arpu.toFixed(2)),
        Churn_Risk: exportChurnLabel(segment),
        Preferred_Channel: channels[rowIndex % channels.length]
      })
    }
  })

  return rows
}

function buildTargetedCustomerCsv(filters?: CustomerExportFilters) {
  const headers = [
    'Customer_ID',
    'Full_Name',
    'Phone_Number',
    'Email',
    'Region',
    'City',
    'Business_Segment',
    'ARPU_TND',
    'ARPU_DT',
    'Churn_Risk',
    'Preferred_Channel'
  ]
  const rows = buildTargetedCustomerRows(filters)

  return [
    headers.join(','),
    ...rows.map((row) => headers.map((header) => csvEscape(row[header] ?? '')).join(','))
  ].join('\n')
}

function buildTargetedCustomerExcelHtml(filters?: CustomerExportFilters) {
  const headers = [
    'Customer_ID',
    'Full_Name',
    'Phone_Number',
    'Email',
    'Region',
    'City',
    'Business_Segment',
    'ARPU_TND',
    'ARPU_DT',
    'Churn_Risk',
    'Preferred_Channel'
  ]
  const rows = buildTargetedCustomerRows(filters)

  return `<!doctype html><html><head><meta charset="utf-8" /></head><body><table><thead><tr>${headers.map((header) => `<th>${xmlEscape(header)}</th>`).join('')}</tr></thead><tbody>${rows.map((row) => `<tr>${headers.map((header) => `<td>${xmlEscape(row[header])}</td>`).join('')}</tr>`).join('')}</tbody></table></body></html>`
}

function buildSegmentCsv() {
  const headers = ['business_segment', 'customers', 'market_share_pct', 'arpu_dt_tnd', 'data_usage_gb', 'voice_minutes', 'international_minutes', 'tenure_months', 'warnings', 'churn_risk_label', 'churn_risk_pct']
  const rows = getReportSegments().map((segment) => [
    segment.name,
    segment.customers,
    segment.share,
    segment.arpu,
    segment.dataUsage,
    segment.voiceMinutes,
    segment.internationalMinutes,
    segment.tenure,
    segment.validationWarnings.length,
    exportChurnLabel(segment),
    exportChurnPct(segment)
  ])

  return [headers.join(','), ...rows.map((row) => row.map(csvEscape).join(','))].join('\n')
}

function buildSqlDump() {
  const insertRows = getReportSegments()
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
        exportChurnLabel(segment),
        exportChurnPct(segment)
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
  const reportSegments = getReportSegments()
  const metrics = getReportMetrics(reportSegments)
  const lines = [
    `SmartSeg ${getSegmentationLevelLabel()} Report`,
    `Generated: ${new Date().toLocaleString()}`,
    '',
    `Total Customers: ${metrics.totalCustomers.toLocaleString()}`,
    `Optimal Clusters: ${metrics.numSegments}`,
    `Model Accuracy: ${metrics.modelAccuracy}%`,
    `Silhouette Score: ${metrics.silhouetteScore ?? 'N/A'}`,
    '',
    'Segments:'
  ]

  for (const segment of reportSegments) {
    lines.push(`- ${segment.name}: ${segment.customers.toLocaleString()} customers | ARPU ${segment.arpu} DT/TND`)
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

function sanitizePdfText(text: string | number) {
  return String(text)
    .normalize('NFKD')
    .replace(/[^\x20-\x7E]/g, '')
    .replace(/\\/g, '\\\\')
    .replace(/\(/g, '\\(')
    .replace(/\)/g, '\\)')
}

function wrapPdfText(text: string, maxChars = 92) {
  const words = text.split(/\s+/).filter(Boolean)
  const lines: string[] = []
  let current = ''

  for (const word of words) {
    const next = current ? `${current} ${word}` : word
    if (next.length > maxChars && current) {
      lines.push(current)
      current = word
    } else {
      current = next
    }
  }

  if (current) {
    lines.push(current)
  }

  return lines.length > 0 ? lines : ['']
}

type PdfLine = {
  text: string
  size?: number
  bold?: boolean
  gapBefore?: number
}

function buildPdfLines(): PdfLine[] {
  const reportSegments = getReportSegments()
  const metrics = getReportMetrics(reportSegments)
  const lines: PdfLine[] = [
    { text: `SmartSeg ${getSegmentationLevelLabel()} Report`, size: 22, bold: true },
    { text: `Generated ${new Date().toLocaleString()}`, size: 10 },
    { text: 'Executive Summary', size: 15, bold: true, gapBefore: 18 },
    {
      text: `This report summarizes ${reportSegments.length} business segments across ${metrics.totalCustomers.toLocaleString()} customers. K-Means creates mathematical clusters first; SmartSeg then names and aggregates clusters with the same telecom business meaning.`
    },
    { text: 'Key Metrics', size: 15, bold: true, gapBefore: 14 },
    { text: `Total customers: ${metrics.totalCustomers.toLocaleString()}` },
    { text: `Segments: ${metrics.numSegments}` },
    { text: `Model accuracy: ${metrics.modelAccuracy}%` },
    { text: `Silhouette score: ${metrics.silhouetteScore ?? 'N/A'}` },
    { text: `Davies-Bouldin score: ${metrics.daviesBouldinScore ?? 'N/A'}` },
    { text: `Calinski-Harabasz score: ${metrics.calinskiHarabaszScore ?? 'N/A'}` },
    { text: 'Segment Profiles', size: 15, bold: true, gapBefore: 14 }
  ]

  for (const segment of reportSegments) {
    lines.push(
      { text: segment.name, size: 13, bold: true, gapBefore: 10 },
      {
        text: `${segment.customers.toLocaleString()} customers | ${segment.share}% share | ARPU ${segment.arpu.toFixed(2)} DT/TND | ${segment.dataUsage} GB/mo | ${segment.voiceMinutes} voice min/mo | ${segment.tenure} months tenure${exportChurnSummary(segment)}`
      }
    )

    for (const characteristic of segment.characteristics.slice(0, 4)) {
      lines.push({ text: `- ${characteristic}`, size: 10 })
    }
  }

  lines.push({ text: 'Report Sections', size: 15, bold: true, gapBefore: 14 })
  for (const section of reportSections) {
    lines.push({ text: `${section.ready ? 'Ready' : 'Pending'} - ${section.name} (${section.pages} pages)`, size: 10 })
  }

  lines.push(
    { text: 'Recommended Next Steps', size: 15, bold: true, gapBefore: 14 },
    { text: '1. Prioritize high-risk customer segments with retention offers and service recovery workflows.' },
    { text: '2. Build premium upsell journeys for high-value and data-driven customers.' },
    { text: '3. Monitor segment movement monthly and refresh clustering after major campaign cycles.' }
  )

  return lines
}

function createPdfContent(lines: PdfLine[]) {
  const pageWidth = 595
  const pageHeight = 842
  const marginX = 50
  const startY = 790
  const bottomY = 55
  const pages: string[][] = [[]]
  let y = startY

  const addPage = () => {
    pages.push([])
    y = startY
  }

  for (const line of lines) {
    const size = line.size ?? 11
    const lineHeight = Math.max(14, size + 5)
    const gapBefore = line.gapBefore ?? 0
    const wrappedLines = wrapPdfText(line.text, size >= 18 ? 42 : size >= 14 ? 62 : 92)

    if (y - gapBefore - wrappedLines.length * lineHeight < bottomY) {
      addPage()
    }

    y -= gapBefore

    for (const wrappedLine of wrappedLines) {
      if (y < bottomY) {
        addPage()
      }

      const font = line.bold ? 'F2' : 'F1'
      pages[pages.length - 1].push(`BT /${font} ${size} Tf ${marginX} ${y} Td (${sanitizePdfText(wrappedLine)}) Tj ET`)
      y -= lineHeight
    }
  }

  const objects: string[] = []
  const pageObjectIds: number[] = []
  objects.push('<< /Type /Catalog /Pages 2 0 R >>')
  objects.push('')
  objects.push('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>')
  objects.push('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>')

  for (const pageLines of pages) {
    const contentObjectId = objects.length + 1
    const content = pageLines.join('\n')
    objects.push(`<< /Length ${content.length} >>\nstream\n${content}\nendstream`)

    const pageObjectId = objects.length + 1
    pageObjectIds.push(pageObjectId)
    objects.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${pageWidth} ${pageHeight}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents ${contentObjectId} 0 R >>`)
  }

  objects[1] = `<< /Type /Pages /Count ${pageObjectIds.length} /Kids [${pageObjectIds.map((id) => `${id} 0 R`).join(' ')}] >>`

  let pdf = '%PDF-1.4\n'
  const offsets = [0]

  objects.forEach((object, index) => {
    offsets.push(pdf.length)
    pdf += `${index + 1} 0 obj\n${object}\nendobj\n`
  })

  const xrefOffset = pdf.length
  pdf += `xref\n0 ${objects.length + 1}\n`
  pdf += '0000000000 65535 f \n'
  for (const offset of offsets.slice(1)) {
    pdf += `${String(offset).padStart(10, '0')} 00000 n \n`
  }
  pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`

  return pdf
}

function createPdfBlob(lines: PdfLine[]) {
  return new Blob([createPdfContent(lines)], { type: 'application/pdf' })
}

function columnName(index: number) {
  let name = ''
  let cursor = index

  while (cursor > 0) {
    const remainder = (cursor - 1) % 26
    name = String.fromCharCode(65 + remainder) + name
    cursor = Math.floor((cursor - 1) / 26)
  }

  return name
}

function createXlsxBytes() {
  const reportSegments = getReportSegments()
  const metrics = getReportMetrics(reportSegments)
  const headers = [
    'Segment',
    'Customers',
    'Market Share %',
    'ARPU DT/TND',
    'Data Usage GB',
    'Voice Minutes',
    'International Minutes',
    'Tenure Months',
    'Validation Warnings',
    'Churn Risk',
    'Churn Risk %'
  ]
  const rows = [
    headers,
    ...reportSegments.map((segment) => [
      segment.name,
      segment.customers,
      segment.share,
      Number(segment.arpu.toFixed(2)),
      Number(segment.dataUsage.toFixed(2)),
      Number(segment.voiceMinutes.toFixed(2)),
      Number(segment.internationalMinutes.toFixed(2)),
      Number(segment.tenure.toFixed(2)),
      segment.validationWarnings.length,
      exportChurnLabel(segment),
      exportChurnPct(segment)
    ]),
    [],
    ['Generated', new Date().toLocaleString()],
    ['Total Customers', metrics.totalCustomers],
    ['Segments', metrics.numSegments],
    ['Model Accuracy %', metrics.modelAccuracy],
    ['Silhouette Score', metrics.silhouetteScore ?? 'N/A'],
    ['Davies-Bouldin Score', metrics.daviesBouldinScore ?? 'N/A'],
    ['Calinski-Harabasz Score', metrics.calinskiHarabaszScore ?? 'N/A']
  ]

  const sheetRows = rows
    .map((row, rowIndex) => {
      const rowNumber = rowIndex + 1
      const cells = row
        .map((value, cellIndex) => {
          const ref = `${columnName(cellIndex + 1)}${rowNumber}`
          if (typeof value === 'number' && Number.isFinite(value)) {
            return `<c r="${ref}"><v>${value}</v></c>`
          }
          return `<c r="${ref}" t="inlineStr"><is><t>${xmlEscape(value)}</t></is></c>`
        })
        .join('')

      return `<row r="${rowNumber}">${cells}</row>`
    })
    .join('')

  const worksheet = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <cols>
    <col min="1" max="1" width="26" customWidth="1"/>
    <col min="2" max="9" width="16" customWidth="1"/>
  </cols>
  <sheetData>${sheetRows}</sheetData>
</worksheet>`

  return createZipBytes([
    {
      path: '[Content_Types].xml',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>`
    },
    {
      path: '_rels/.rels',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>`
    },
    {
      path: 'xl/workbook.xml',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Segments" sheetId="1" r:id="rId1"/></sheets>
</workbook>`
    },
    {
      path: 'xl/_rels/workbook.xml.rels',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>`
    },
    {
      path: 'xl/worksheets/sheet1.xml',
      content: worksheet
    },
    {
      path: 'xl/styles.xml',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="1"><fill><patternFill patternType="none"/></fill></fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>`
    },
    {
      path: 'docProps/core.xml',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>SmartSeg Segment Data Export</dc:title>
  <dc:creator>SmartSeg</dc:creator>
  <dcterms:created xsi:type="dcterms:W3CDTF">${new Date().toISOString()}</dcterms:created>
</cp:coreProperties>`
    },
    {
      path: 'docProps/app.xml',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>SmartSeg</Application></Properties>`
    }
  ])
}

function pptTextBox(id: number, name: string, x: number, y: number, w: number, h: number, text: string, size = 2200, bold = false) {
  return `<p:sp>
  <p:nvSpPr><p:cNvPr id="${id}" name="${xmlEscape(name)}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
  <p:spPr><a:xfrm><a:off x="${x}" y="${y}"/><a:ext cx="${w}" cy="${h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
  <p:txBody><a:bodyPr wrap="square"/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="${size}"${bold ? ' b="1"' : ''}/><a:t>${xmlEscape(text)}</a:t></a:r></a:p></p:txBody>
</p:sp>`
}

function createSlideXml(title: string, bodyLines: string[]) {
  const bodyText = bodyLines.join('\n')
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      ${pptTextBox(2, 'Title', 457200, 274320, 8229600, 914400, title, 3000, true)}
      ${pptTextBox(3, 'Body', 457200, 1371600, 8229600, 4572000, bodyText, 1700)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>`
}

function createPptxBytes() {
  const reportSegments = getReportSegments()
  const metrics = getReportMetrics(reportSegments)
  const slides = [
    createSlideXml(`SmartSeg ${getSegmentationLevelLabel()} Report`, [
      `Generated: ${new Date().toLocaleString()}`,
      `Total customers: ${metrics.totalCustomers.toLocaleString()}`,
      `Segments: ${metrics.numSegments}`,
      `Model accuracy: ${metrics.modelAccuracy}%`,
      `Silhouette score: ${metrics.silhouetteScore ?? 'N/A'}`
    ]),
    createSlideXml('Segment Overview', reportSegments.map((segment) => `${segment.name}: ${segment.customers.toLocaleString()} customers, ${segment.share}% share, ARPU ${segment.arpu.toFixed(2)} DT/TND${exportChurnSummary(segment)}`)),
    createSlideXml('Recommended Actions', [
      'Prioritize critical and high-risk segments with retention workflows.',
      'Build premium upsell journeys for high-value and data-driven customers.',
      'Track campaign response and refresh segments after major campaigns.'
    ])
  ]

  const slideOverrides = slides
    .map((_, index) => `<Override PartName="/ppt/slides/slide${index + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>`)
    .join('')
  const slideRelationships = slides
    .map((_, index) => `<Relationship Id="rId${index + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide${index + 1}.xml"/>`)
    .join('')
  const slideIds = slides
    .map((_, index) => `<p:sldId id="${256 + index}" r:id="rId${index + 2}"/>`)
    .join('')

  return createZipBytes([
    {
      path: '[Content_Types].xml',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  ${slideOverrides}
</Types>`
    },
    {
      path: '_rels/.rels',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>`
    },
    {
      path: 'ppt/presentation.xml',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>${slideIds}</p:sldIdLst>
  <p:sldSz cx="9144000" cy="5143500" type="screen16x9"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>`
    },
    {
      path: 'ppt/_rels/presentation.xml.rels',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
  ${slideRelationships}
</Relationships>`
    },
    {
      path: 'ppt/slideMasters/slideMaster1.xml',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
</p:sldMaster>`
    },
    {
      path: 'ppt/slideMasters/_rels/slideMaster1.xml.rels',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>`
    },
    {
      path: 'ppt/slideLayouts/slideLayout1.xml',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>`
    },
    {
      path: 'ppt/slideLayouts/_rels/slideLayout1.xml.rels',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>`
    },
    {
      path: 'ppt/theme/theme1.xml',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="SmartSeg">
  <a:themeElements>
    <a:clrScheme name="SmartSeg"><a:dk1><a:srgbClr val="0F172A"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="334155"/></a:dk2><a:lt2><a:srgbClr val="F8FAFC"/></a:lt2><a:accent1><a:srgbClr val="CD2027"/></a:accent1><a:accent2><a:srgbClr val="2563EB"/></a:accent2><a:accent3><a:srgbClr val="16A34A"/></a:accent3><a:accent4><a:srgbClr val="F59E0B"/></a:accent4><a:accent5><a:srgbClr val="8B5CF6"/></a:accent5><a:accent6><a:srgbClr val="64748B"/></a:accent6><a:hlink><a:srgbClr val="2563EB"/></a:hlink><a:folHlink><a:srgbClr val="7C3AED"/></a:folHlink></a:clrScheme>
    <a:fontScheme name="SmartSeg"><a:majorFont><a:latin typeface="Arial"/></a:majorFont><a:minorFont><a:latin typeface="Arial"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="SmartSeg"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements>
</a:theme>`
    },
    ...slides.flatMap((slide, index) => [
      { path: `ppt/slides/slide${index + 1}.xml`, content: slide },
      {
        path: `ppt/slides/_rels/slide${index + 1}.xml.rels`,
        content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>`
      }
    ]),
    {
      path: 'docProps/core.xml',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>SmartSeg Strategic Insights Deck</dc:title>
  <dc:creator>SmartSeg</dc:creator>
  <dcterms:created xsi:type="dcterms:W3CDTF">${new Date().toISOString()}</dcterms:created>
</cp:coreProperties>`
    },
    {
      path: 'docProps/app.xml',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>SmartSeg</Application><Slides>${slides.length}</Slides></Properties>`
    }
  ])
}

export function downloadReportPdf() {
  downloadBlobFile('Customer_Segmentation_Report.pdf', createPdfBlob(buildPdfLines()))
}

export function downloadPowerPoint() {
  downloadBlobFile(
    'Strategic_Insights_Deck.pptx',
    new Blob([createPptxBytes()], {
      type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    })
  )
}

export function downloadExcel() {
  downloadBlobFile(
    'Segment_Data_Export.xlsx',
    new Blob([createXlsxBytes()], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
  )
}

export function downloadCsv() {
  downloadTextFile('segments.csv', buildSegmentCsv(), 'text/csv;charset=utf-8')
}

export async function downloadTargetedCustomersCsv(filters: CustomerExportFilters = {}) {
  await downloadTargetedCustomers(filters, 'csv')
}

export async function downloadTargetedCustomersExcel(filters: CustomerExportFilters = {}) {
  await downloadTargetedCustomers(filters, 'excel')
}

export function downloadJson(options?: ExportOptions) {
  const reportSegments = getReportSegments()
  const metrics = getReportMetrics(reportSegments)
  const payload = {
    metadata: {
      generated_at: new Date().toISOString(),
      total_customers: metrics.totalCustomers,
      segment_count: metrics.numSegments,
      model_accuracy: metrics.modelAccuracy / 100,
      report_type: getSegmentationLevelLabel(),
      silhouette_score: metrics.silhouetteScore,
      davies_bouldin_score: metrics.daviesBouldinScore,
      calinski_harabasz_score: metrics.calinskiHarabaszScore
    },
    export_options: options,
    segments: reportSegments.map((segment) => ({
      id: segment.id,
      name: segment.name,
      customers: segment.customers,
      market_share_pct: segment.share,
      arpu: segment.arpu,
      data_usage_gb: segment.dataUsage,
      voice_minutes: segment.voiceMinutes,
      international_minutes: segment.internationalMinutes,
      tenure: segment.tenure,
      tenure_unit: segment.tenureUnit,
      churn_risk_label: exportChurnLabel(segment),
      churn_risk_pct: exportChurnPct(segment),
      validation_warnings: segment.validationWarnings
    }))
  }

  downloadTextFile('segments.json', JSON.stringify(payload, null, 2), 'application/json;charset=utf-8')
}

export function downloadSql() {
  downloadTextFile('segments_dump.sql', buildSqlDump(), 'application/sql;charset=utf-8')
}

export function downloadBatchPackage(options: ExportOptions) {
  const manifest = {
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

  const reportPdf = createPdfContent(buildPdfLines())
  const entries: ZipEntry[] = [
    { path: 'Customer_Segmentation_Report.pdf', content: reportPdf },
    { path: 'Strategic_Insights_Deck.pptx', content: createPptxBytes() },
    { path: 'Segment_Data_Export.xlsx', content: createXlsxBytes() },
    {
      path: 'segments.json',
      content: JSON.stringify({
        metadata: {
          generated_at: new Date().toISOString(),
          total_customers: getReportMetrics().totalCustomers,
          segment_count: getReportMetrics().numSegments
        },
        export_options: options,
        segments: getReportSegments()
      }, null, 2)
    },
    { path: 'segments.csv', content: buildSegmentCsv() },
    { path: 'segments_dump.sql', content: buildSqlDump() },
    { path: 'manifest.json', content: JSON.stringify(manifest, null, 2) }
  ]

  downloadBlobFile('smartseg_export_package.zip', createZipBlob(entries))
}

export function openEmailDraft() {
  const subject = encodeURIComponent(`SmartSeg ${getSegmentationLevelLabel()} Report`)
  const body = encodeURIComponent('Please find the attached SmartSeg segmentation report package.\n\nRegards,\nMarketing Analytics')
  window.location.href = `mailto:?subject=${subject}&body=${body}`
}

export function printPreview() {
  window.print()
}
