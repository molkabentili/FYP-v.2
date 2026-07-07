/**
 * Display adapter for backend-provided business segments.
 *
 * Segment names are assigned by the backend business segmentation module.
 * The frontend only maps those business_segment values into UI cards.
 */

export const EXPECTED_SEGMENTATION_RULE_VERSION = 'business-v5-revenue-weighted-value'

export function clearStaleSegmentationStorage(): void {
  sessionStorage.removeItem('smartseg_clustering_results')
  sessionStorage.removeItem('smartseg_run_id')
  localStorage.removeItem('smartseg_clustering_results')
  localStorage.removeItem('smartseg_run_id')
}

export interface DisplaySegment {
  id: string
  clusterId: number | string
  sourceClusterIds: number[]
  name: string
  valueSegmentName: string
  segmentDescription: string
  color: string
  customers: number
  arpu: number
  share: number
  dataUsage: number
  voiceMinutes: number
  tenure: number
  tenureUnit: 'months'
  internationalMinutes: number
  complaints: number
  satisfaction: number
  latePayments: number
  clv: number
  characteristics: string[]
  validationWarnings: string[]
  churnRiskPct: number
  churnRiskLabel: 'Low' | 'Medium' | 'High' | 'Critical'
  showChurnRisk: boolean
}

export type SegmentViewMode = 'auto' | 'value' | 'business' | 'detailed'

type BackendBusinessSegment = {
  business_segment?: string
  name?: string
  customer_count?: number
  customers?: number
  percentage?: number
  share?: number
  avg_arpu?: number
  arpu?: number
  avg_data_usage?: number
  data_usage?: number
  avg_voice_minutes?: number
  voice_minutes?: number
  avg_international_minutes?: number
  international_minutes?: number
  avg_tenure_months?: number
  tenure_months?: number
  avg_churn_probability?: number
  churn_probability?: number
  avg_satisfaction?: number
  satisfaction?: number
  avg_complaints?: number
  complaints?: number
  avg_late_payments?: number
  late_payments?: number
  avg_clv?: number
  clv?: number
  value_score?: number
  risk_score?: number
  rule_version?: string
  naming_source?: string
  source_cluster_ids?: number[]
  validation_warnings?: string[]
}

const BUSINESS_SEGMENT_ORDER = [
  'At Risk Customers',
  'International Customers',
  'Data Driven Customers',
  'Premium Customers',
  'High Value Customers',
  'Growth Potential Customers',
  'Medium Value Customers',
  'Low Value Customers'
] as const

type BusinessSegmentName = (typeof BUSINESS_SEGMENT_ORDER)[number]

const BUSINESS_SEGMENT_COLORS: Record<BusinessSegmentName, string> = {
  'At Risk Customers': '#ef4444',
  'International Customers': '#db2777',
  'Data Driven Customers': '#2563eb',
  'Premium Customers': '#7c3aed',
  'High Value Customers': '#16a34a',
  'Growth Potential Customers': '#0891b2',
  'Medium Value Customers': '#3b82f6',
  'Low Value Customers': '#f59e0b'
}

function toNumber(value: unknown, fallback = 0): number {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : fallback
  }
  return fallback
}

function toBusinessSegmentName(name: unknown): BusinessSegmentName | null {
  return BUSINESS_SEGMENT_ORDER.includes(name as BusinessSegmentName)
    ? name as BusinessSegmentName
    : null
}

function getBusinessSegmentDescription(segmentName: BusinessSegmentName): string {
  switch (segmentName) {
    case 'At Risk Customers':
      return 'Customers with strong risk indicators from churn probability, satisfaction, complaints, late payments, or severe inactivity.'
    case 'International Customers':
      return 'Customers with high international call activity and meaningful revenue contribution.'
    case 'Data Driven Customers':
      return 'Customers with very high data usage, lower voice intensity, and sufficient ARPU.'
    case 'Premium Customers':
      return 'Very high ARPU customers with heavy data usage.'
    case 'High Value Customers':
      return 'Strong revenue or lifetime-value customers.'
    case 'Growth Potential Customers':
      return 'Active medium-ARPU customers with strong usage, acceptable satisfaction, and manageable churn risk.'
    case 'Medium Value Customers':
      return 'Normal average customers after higher-priority international, data-driven, premium, high-value, and growth rules are checked.'
    case 'Low Value Customers':
      return 'Lowest revenue or fallback low-usage customers.'
  }
}

function getBusinessSegmentActions(segmentName: BusinessSegmentName): string[] {
  switch (segmentName) {
    case 'At Risk Customers':
      return ['Retention campaigns', 'Service recovery', 'Loyalty incentives']
    case 'International Customers':
      return ['International call bundles', 'Roaming offers', 'Travel packages']
    case 'Data Driven Customers':
      return ['Larger data bundles', '5G upgrades', 'Streaming offers']
    case 'Premium Customers':
      return ['VIP care', 'Premium plan protection', 'Exclusive high-data bundles']
    case 'High Value Customers':
      return ['Loyalty rewards', 'Device offers', 'Cross-sell campaigns']
    case 'Growth Potential Customers':
      return ['Upgrade offers', 'Personalized bundle recommendations', 'Loyalty nudges']
    case 'Medium Value Customers':
      return ['Bundle optimization', 'Gradual upsell offers', 'Lifecycle campaigns']
    case 'Low Value Customers':
      return ['Basic bundles', 'Efficient prepaid offers', 'Low-cost recharge campaigns']
  }
}

function churnRiskLabel(churnRiskPct: number): DisplaySegment['churnRiskLabel'] {
  if (churnRiskPct >= 70) return 'Critical'
  if (churnRiskPct >= 60) return 'High'
  if (churnRiskPct >= 20) return 'Medium'
  return 'Low'
}

export function shouldShowChurnRisk(segment: { name: string }): boolean {
  return segment.name === 'At Risk Customers'
}

export function formatAtRiskChurn(segment: { name: string; churnRiskPct: number }): string {
  return shouldShowChurnRisk(segment) ? `${segment.churnRiskPct.toFixed(1)}%` : 'N/A'
}

function mapBusinessSegment(segment: BackendBusinessSegment): DisplaySegment | null {
  const businessName = toBusinessSegmentName(segment.business_segment ?? segment.name)
  if (!businessName) return null

  const sourceClusterIds = Array.isArray(segment.source_cluster_ids)
    ? segment.source_cluster_ids.map((clusterId) => Number(clusterId)).filter(Number.isFinite)
    : []
  const share = toNumber(segment.percentage ?? segment.share)
  const rawChurnRiskPct = toNumber(segment.avg_churn_probability ?? segment.churn_probability)
  const showChurnRisk = businessName === 'At Risk Customers'
  // In the UI, the At Risk churn percentage is the percentage of customers
  // assigned to the At Risk business segment. Raw churn probability remains a
  // backend metric, but it may be absent/0 in datasets that use risk ranking.
  const churnRiskPct = showChurnRisk ? share : rawChurnRiskPct

  return {
    id: `business-${businessName.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`,
    clusterId: sourceClusterIds.join(', '),
    sourceClusterIds,
    name: businessName,
    valueSegmentName: businessName,
    segmentDescription: getBusinessSegmentDescription(businessName),
    color: BUSINESS_SEGMENT_COLORS[businessName],
    customers: toNumber(segment.customer_count ?? segment.customers),
    arpu: toNumber(segment.avg_arpu ?? segment.arpu),
    share,
    dataUsage: toNumber(segment.avg_data_usage ?? segment.data_usage),
    voiceMinutes: toNumber(segment.avg_voice_minutes ?? segment.voice_minutes),
    tenure: toNumber(segment.avg_tenure_months ?? segment.tenure_months),
    tenureUnit: 'months',
    internationalMinutes: toNumber(segment.avg_international_minutes ?? segment.international_minutes),
    complaints: toNumber(segment.avg_complaints ?? segment.complaints),
    satisfaction: toNumber(segment.avg_satisfaction ?? segment.satisfaction),
    latePayments: toNumber(segment.avg_late_payments ?? segment.late_payments),
    clv: toNumber(segment.avg_clv ?? segment.clv),
    characteristics: [
      `Source clusters: ${sourceClusterIds.length > 0 ? sourceClusterIds.join(', ') : 'N/A'}`,
      `Naming source: ${segment.naming_source ?? 'backend/business_segmentation.py'}`,
      `Rule version: ${segment.rule_version ?? EXPECTED_SEGMENTATION_RULE_VERSION}`,
      'Weighted averages calculated by customer count',
      ...getBusinessSegmentActions(businessName)
    ],
    validationWarnings: Array.isArray(segment.validation_warnings) ? segment.validation_warnings : [],
    churnRiskPct,
    churnRiskLabel: churnRiskLabel(churnRiskPct),
    showChurnRisk
  }
}

function getBackendSegments(clusteringResults: any): BackendBusinessSegment[] {
  if (clusteringResults?.segmentation_rule_version !== EXPECTED_SEGMENTATION_RULE_VERSION) {
    return []
  }

  if (Array.isArray(clusteringResults?.business_segments)) {
    return clusteringResults.business_segments
  }

  return []
}

/**
 * Transform backend business segments into display cards.
 */
export function transformClusteringResults(clusteringResults: any, _mode: SegmentViewMode = 'auto'): DisplaySegment[] {
  const mapped = getBackendSegments(clusteringResults)
    .map(mapBusinessSegment)
    .filter((segment): segment is DisplaySegment => segment !== null)

  return BUSINESS_SEGMENT_ORDER
    .map((segmentName) => mapped.find((segment) => segment.name === segmentName))
    .filter((segment): segment is DisplaySegment => Boolean(segment))
}

/**
 * Get business segments from sessionStorage.
 */
export function getDisplaySegments(mode: SegmentViewMode = 'auto'): DisplaySegment[] {
  try {
    const stored = sessionStorage.getItem('smartseg_clustering_results')
    if (stored) {
      const parsed = JSON.parse(stored)
      if (parsed?.segmentation_rule_version !== EXPECTED_SEGMENTATION_RULE_VERSION) {
        clearStaleSegmentationStorage()
        return []
      }
      return transformClusteringResults(parsed, mode)
    }
  } catch (error) {
    console.error('Error loading clustering results:', error)
  }
  return []
}
