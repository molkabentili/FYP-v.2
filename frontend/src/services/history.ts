import type { ClusteringResponse } from './api'

const HISTORY_STORAGE_KEY = 'smartseg_run_history'
const MAX_HISTORY_ITEMS = 10

export type SmartSegRunParameters = {
  algorithm: 'kmeans'
  k: number
  autoK: boolean
  preprocessing: {
    normalization: boolean
    handleMissing: boolean
    outlier: boolean
    scaling: boolean
    imputation: 'median' | 'mean' | 'most_frequent'
  }
  selectedFeatures: string[]
}

export type SmartSegRunHistoryItem = {
  id: string
  createdAt: string
  datasetId: string | null
  preprocessedFile: string | null
  parameters: SmartSegRunParameters
  results: ClusteringResponse
  summary: {
    k: number
    algorithm: string
    businessSegments: number
    customers: number
    ruleVersion?: string
  }
}

function parseHistory(raw: string | null): SmartSegRunHistoryItem[] {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function readRunHistory(): SmartSegRunHistoryItem[] {
  return parseHistory(window.localStorage.getItem(HISTORY_STORAGE_KEY))
}

export function saveRunHistory(item: SmartSegRunHistoryItem): void {
  const history = readRunHistory()
  const nextHistory = [
    item,
    ...history.filter((existing) => existing.id !== item.id)
  ].slice(0, MAX_HISTORY_ITEMS)

  window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(nextHistory))
}

export function restoreRunHistoryItem(item: SmartSegRunHistoryItem): void {
  window.sessionStorage.setItem('smartseg_run_id', item.id)
  window.sessionStorage.setItem('smartseg_clustering_results', JSON.stringify(item.results))
  window.sessionStorage.setItem('smartseg_run_parameters', JSON.stringify(item.parameters))

  if (item.datasetId) {
    window.sessionStorage.setItem('smartseg_dataset_id', item.datasetId)
  }
  if (item.preprocessedFile) {
    window.sessionStorage.setItem('smartseg_preprocessed_file', item.preprocessedFile)
  }
}
