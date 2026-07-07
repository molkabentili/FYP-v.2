export type Segment = {
  id: string
  name: string
  color: string
  customers: number
  share: number
  arpu: number
  dataUsage: number
  voiceMinutes: number
  tenure: number
  churnRiskLabel: 'Low' | 'Medium' | 'High' | 'Critical'
  churnRiskPct: number
  characteristics: string[]
  strategies: {
    retention: string[]
    upselling: string[]
    campaigns: string[]
  }
}

export const platformMetrics = {
  totalCustomers: 15400,
  modelAccuracy: 87,
  silhouetteScore: 0.68,
  optimalClusters: 4
}

export const segments: Segment[] = [
  {
    id: 'high-value',
    name: 'High Value Customers',
    color: '#22c55e',
    customers: 2847,
    share: 18.5,
    arpu: 127.45,
    dataUsage: 45.2,
    voiceMinutes: 780,
    tenure: 4.2,
    churnRiskLabel: 'Low',
    churnRiskPct: 8,
    characteristics: [
      'Highest ARPU and premium service mix',
      'Long tenure and loyalty program participation',
      'High data and voice usage patterns',
      'Strong VAS and content engagement',
      'High digital channel adoption',
      'Low complaint frequency'
    ],
    strategies: {
      retention: ['VIP service line', 'Early access programs', 'Premium loyalty tiers', 'Executive check-ins'],
      upselling: ['Family premium bundles', 'International roaming packs', '5G premium add-ons', 'Exclusive content plans'],
      campaigns: ['Anniversary appreciation offers', 'Referral elite rewards', 'Premium influencer campaigns']
    }
  },
  {
    id: 'data-driven',
    name: 'Data Driven Customers',
    color: '#3b82f6',
    customers: 4521,
    share: 29.3,
    arpu: 78.32,
    dataUsage: 62.8,
    voiceMinutes: 320,
    tenure: 2.1,
    churnRiskLabel: 'Medium',
    churnRiskPct: 22,
    characteristics: [
      'Largest mobile data consumers',
      'Video and social streaming heavy',
      'Mid-range ARPU with upsell potential',
      'High demand for network speed',
      'Responsive to digital bundles',
      'Price-sensitive to data overage'
    ],
    strategies: {
      retention: ['Data loyalty rewards', 'Proactive QoS support', 'Usage alerts and controls', 'Night-time unlimited perks'],
      upselling: ['Unlimited data plans', 'Speed boost options', 'Content partnerships', 'Data rollover upgrades'],
      campaigns: ['Streamer bundle campaigns', 'Gaming sponsorship offers', 'Social media challenge promotions']
    }
  },
  {
    id: 'medium-value',
    name: 'Medium Value Customers',
    color: '#f59e0b',
    customers: 5234,
    share: 34,
    arpu: 32.18,
    dataUsage: 8.5,
    voiceMinutes: 450,
    tenure: 1.5,
    churnRiskLabel: 'High',
    churnRiskPct: 38,
    characteristics: [
      'Price-sensitive value seekers',
      'Prefer affordable and prepaid plans',
      'Moderate voice and low data usage',
      'High responsiveness to discounts',
      'Shorter average tenure',
      'High migration potential to postpaid'
    ],
    strategies: {
      retention: ['Flexible top-up rewards', 'Affordable loyalty bundles', 'Bill shock prevention alerts', 'Community care outreach'],
      upselling: ['Entry postpaid migration', 'Lite data add-ons', 'Family shared discounts', 'Voice-data hybrid packs'],
      campaigns: ['Seasonal discount campaigns', 'Referral bonus drives', 'Community partnership promotions']
    }
  },
  {
    id: 'at-risk',
    name: 'At Risk Customers',
    color: '#ef4444',
    customers: 2798,
    share: 18.2,
    arpu: 45.67,
    dataUsage: 15.3,
    voiceMinutes: 380,
    tenure: 0.8,
    churnRiskLabel: 'Critical',
    churnRiskPct: 67,
    characteristics: [
      'High complaint and support contact rates',
      'Early-tenure customers with weak attachment',
      'Moderate usage but low satisfaction',
      'High negative sentiment indicators',
      'Frequent plan downgrades',
      'Immediate retention intervention required'
    ],
    strategies: {
      retention: ['Dedicated win-back desk', 'Priority complaint resolution', 'Service recovery credits', '30-day save plan'],
      upselling: ['Trust-building value bundles', 'Assurance-based add-ons', 'Usage-matched plan correction', 'Contract flexibility options'],
      campaigns: ['Apology and recovery campaigns', 'Exit intent interventions', 'High-touch care messaging']
    }
  }
]

export const elbowData = [
  { k: 2, inertia: 14500 },
  { k: 3, inertia: 9300 },
  { k: 4, inertia: 6200 },
  { k: 5, inertia: 5900 },
  { k: 6, inertia: 5650 },
  { k: 7, inertia: 5520 },
  { k: 8, inertia: 5450 }
]

export const silhouetteData = [
  { k: 2, score: 0.49 },
  { k: 3, score: 0.58 },
  { k: 4, score: 0.68 },
  { k: 5, score: 0.61 },
  { k: 6, score: 0.56 },
  { k: 7, score: 0.53 },
  { k: 8, score: 0.5 }
]

export const scatterData = [
  { x: 55, y: 125, segment: 'High Value Customers', color: '#22c55e' },
  { x: 50, y: 132, segment: 'High Value Customers', color: '#22c55e' },
  { x: 44, y: 118, segment: 'High Value Customers', color: '#22c55e' },
  { x: 48, y: 129, segment: 'High Value Customers', color: '#22c55e' },
  { x: 62, y: 82, segment: 'Data Driven Customers', color: '#3b82f6' },
  { x: 71, y: 75, segment: 'Data Driven Customers', color: '#3b82f6' },
  { x: 58, y: 79, segment: 'Data Driven Customers', color: '#3b82f6' },
  { x: 66, y: 84, segment: 'Data Driven Customers', color: '#3b82f6' },
  { x: 11, y: 28, segment: 'Medium Value Customers', color: '#f59e0b' },
  { x: 9, y: 35, segment: 'Medium Value Customers', color: '#f59e0b' },
  { x: 7, y: 30, segment: 'Medium Value Customers', color: '#f59e0b' },
  { x: 10, y: 34, segment: 'Medium Value Customers', color: '#f59e0b' },
  { x: 14, y: 42, segment: 'At Risk Customers', color: '#ef4444' },
  { x: 18, y: 47, segment: 'At Risk Customers', color: '#ef4444' },
  { x: 16, y: 45, segment: 'At Risk Customers', color: '#ef4444' },
  { x: 13, y: 41, segment: 'At Risk Customers', color: '#ef4444' }
]

export const trendData = [
  { month: 'Aug 2025', revenue: 1140, customers: 15120, churn: 23.1 },
  { month: 'Sep 2025', revenue: 1170, customers: 15190, churn: 23.4 },
  { month: 'Oct 2025', revenue: 1195, customers: 15280, churn: 23.9 },
  { month: 'Nov 2025', revenue: 1215, customers: 15340, churn: 24.2 },
  { month: 'Dec 2025', revenue: 1235, customers: 15380, churn: 24.5 },
  { month: 'Jan 2026', revenue: 1248, customers: 15400, churn: 24.8 }
]

export const reportSections = [
  { name: 'Executive Summary', pages: 2, ready: true },
  { name: 'Methodology & Data Quality', pages: 3, ready: true },
  { name: 'Segmentation Analysis', pages: 5, ready: true },
  { name: 'Customer Segment Profiles', pages: 8, ready: true },
  { name: 'Business Strategies', pages: 12, ready: true },
  { name: 'ROI Projections', pages: 4, ready: true },
  { name: 'Implementation Roadmap', pages: 3, ready: true },
  { name: 'Technical Appendix', pages: 6, ready: false }
]
