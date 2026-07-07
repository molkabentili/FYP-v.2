/**
 * Backend API Service
 * Connects frontend to Python FastAPI backend for clustering
 */

import { clearStaleSegmentationStorage, EXPECTED_SEGMENTATION_RULE_VERSION } from './segmentTransform';

declare global {
  interface ImportMeta {
    env: {
      VITE_API_BASE_URL?: string;
      VITE_DEFAULT_AUTH_EMAIL?: string;
      VITE_DEFAULT_AUTH_PASSWORD?: string;
    };
  }
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8099";

const AUTH_STORAGE_KEY = "smartseg_auth";

const DEFAULT_AUTH_EMAIL =
  import.meta.env.VITE_DEFAULT_AUTH_EMAIL || "analyst@ooredoo.com";

const DEFAULT_AUTH_PASSWORD =
  import.meta.env.VITE_DEFAULT_AUTH_PASSWORD || "SmartSeg2026!";

/* =========================
   TYPES
========================= */

export interface UserProfile {
  email: string;
  role: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  user: UserProfile;
}

export interface ClusteringRequest {
  preprocessed_file: string;
  algorithm: "kmeans" | "hierarchical" | "dbscan";
  n_clusters: number;
  linkage?: string;
  eps?: number;
  min_samples?: number;
}

export interface ClusterStats {
  cluster_id: number;
  size: number;
  percentage: number;
  mean_values: Record<string, number>;
}

export interface BusinessCluster {
  cluster_id: number;
  business_segment: string;
  customer_count: number;
  percentage: number;
  avg_arpu: number;
  avg_data_usage: number;
  avg_voice_minutes: number;
  avg_international_minutes: number;
  avg_clv: number;
  avg_satisfaction: number;
  avg_complaints: number;
  avg_late_payments: number;
  avg_tenure_months: number;
  avg_churn_probability: number;
  value_score?: number;
  risk_score?: number;
  rule_version?: string;
  naming_source?: string;
  validation_warnings: string[];
}

export interface BusinessSegment {
  business_segment: string;
  name: string;
  customer_count: number;
  percentage: number;
  source_cluster_ids: number[];
  avg_arpu: number;
  avg_data_usage: number;
  avg_voice_minutes: number;
  avg_international_minutes: number;
  avg_clv: number;
  avg_satisfaction: number;
  avg_complaints: number;
  avg_late_payments: number;
  avg_tenure_months: number;
  avg_churn_probability: number;
  value_score?: number;
  risk_score?: number;
  rule_version?: string;
  naming_source?: string;
  validation_warnings: string[];
}

export interface ClusteringResponse {
  success: boolean;
  algorithm: string;
  configuration: Record<string, unknown>;
  n_clusters: number;
  labels: number[];
  labels_full_count?: number;
  metrics: {
    silhouette_score: number | null;
    davies_bouldin_score: number | null;
    calinski_harabasz_score: number | null;
  };
  cluster_statistics: ClusterStats[];
  segmentation_rule_version?: string;
  clusters: BusinessCluster[];
  business_segments: BusinessSegment[];
  warnings: string[];
  validation: Record<string, unknown>;
  rule_version?: string;
  naming_source?: string;
  output_file: string;
  segmented_csv: string;
  message: string;
}

export interface PreprocessResponse {
  success: boolean;
  output_file: string;
  output_filename?: string;
  cleaned_shape: [number, number];
  message: string;
}

export interface CustomerExportRequest {
  segmented_csv: string;
  export_format?: "csv" | "excel";
  segment?: string;
  region?: string;
  city?: string;
  churn_risk?: string;
  min_arpu?: number;
  max_arpu?: number;
}

/* =========================
   AUTH HELPERS
========================= */

function getAuthHeaders(): Record<string, string> {
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return {};

    const token = (JSON.parse(raw) as { token?: string }).token;
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {};
  }
}

async function ensureAuthHeaders(): Promise<Record<string, string>> {
  const existing = getAuthHeaders();

  if (existing.Authorization) return existing;

  throw new Error("Authentication required. Please log in first.");
}


async function getApiError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    return payload.error_message ?? payload.detail ?? response.statusText;
  } catch {
    return response.statusText;
  }
}

/* =========================
   AUTH
========================= */

export async function loginUser(
  email: string,
  password: string
): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error(await getApiError(response));
  }

  return response.json();
}

/* =========================
   PREPROCESS
========================= */

export async function preprocessDataset(
  file: File,
  datasetName: string = "customer_data"
): Promise<PreprocessResponse> {
  const authHeaders = await ensureAuthHeaders();

  const formData = new FormData();
  formData.append("file", file);
  formData.append("dataset_name", datasetName);

  const response = await fetch(`${API_BASE_URL}/api/preprocess`, {
    method: "POST",
    headers: authHeaders,
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Preprocessing failed: ${await getApiError(response)}`);
  }

  const result = await response.json();

  // normalize backend output
  return {
    ...result,
    output_file: result.output_file ?? result.output_filename,
  };
}

/* =========================
   CLUSTERING
========================= */

export async function runClustering(
  preprocessedFile: string,
  algorithm: "kmeans" | "hierarchical" | "dbscan" = "kmeans",
  nClusters: number = 5
): Promise<ClusteringResponse> {
  const authHeaders = await ensureAuthHeaders();

  const request: ClusteringRequest = {
    preprocessed_file: preprocessedFile,
    algorithm,
    n_clusters: nClusters,
    linkage: "ward",
    eps: 0.5,
    min_samples: 5,
  };

  const response = await fetch(`${API_BASE_URL}/api/cluster`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Clustering failed: ${await getApiError(response)}`);
  }

  const result = await response.json();

  if (result.segmentation_rule_version !== EXPECTED_SEGMENTATION_RULE_VERSION) {
    clearStaleSegmentationStorage();
    throw new Error(
      `Backend is running old SmartSeg segmentation logic (${result.segmentation_rule_version ?? "missing"}). Restart the FastAPI server and rerun clustering.`
    );
  }

  return result;
}

/* =========================
   HEALTH
========================= */

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}

export async function exportCustomers(request: CustomerExportRequest): Promise<Blob> {
  const authHeaders = await ensureAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/api/export/customers`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Customer export failed: ${await getApiError(response)}`);
  }

  return response.blob();
}
