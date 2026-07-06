export type OfferSource = "wttj" | "indeed" | "greenhouse" | "lever" | "manual";
export type OfferStatus = "new" | "reviewed" | "shortlisted" | "archived";
export type ScrapeRunStatus = "pending" | "running" | "done" | "failed";

export interface Offer {
  id: string;
  source: OfferSource;
  external_id: string | null;
  url: string;
  title: string;
  company: string;
  location: string | null;
  remote_type: string | null;
  contract_type: string | null;
  description_raw: string;
  description_parsed: Record<string, unknown> | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  posted_at: string | null;
  status: OfferStatus;
  compatibility_score: number | null;
  notes: string | null;
  scraped_at: string;
  created_at: string;
  updated_at: string;
}

export interface OfferListResponse {
  items: Offer[];
  total: number;
  page: number;
  page_size: number;
}

export interface ScrapeParams {
  sources: OfferSource[];
  keywords: string;
  location: string;
  greenhouse_slugs: string[];
  lever_slugs: string[];
  since?: string | null;
  max_results_per_source: number;
}

export interface ScrapeRun {
  id: string;
  status: ScrapeRunStatus;
  params: Record<string, unknown>;
  offers_found: number;
  offers_new: number;
  offers_duplicates: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface DashboardStats {
  total_offers: number;
  new_offers: number;
  shortlisted_offers: number;
  by_source: Record<string, number>;
  recent_runs: ScrapeRun[];
}

const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  dashboard: () => request<DashboardStats>("/dashboard"),
  listOffers: (params: URLSearchParams) =>
    request<OfferListResponse>(`/offers?${params}`),
  getOffer: (id: string) => request<Offer>(`/offers/${id}`),
  createManual: (data: Partial<Offer>) =>
    request<Offer>("/offers/manual", { method: "POST", body: JSON.stringify(data) }),
  importUrl: (url: string) =>
    request<Offer>("/offers/import-url", {
      method: "POST",
      body: JSON.stringify({ url }),
    }),
  updateOffer: (id: string, data: { status?: OfferStatus; notes?: string }) =>
    request<Offer>(`/offers/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  archiveOffer: (id: string) =>
    request<void>(`/offers/${id}`, { method: "DELETE" }),
  createScrapeRun: (params: ScrapeParams, saveConfigAs?: string) =>
    request<ScrapeRun>("/scrape-runs", {
      method: "POST",
      body: JSON.stringify({ params, save_config_as: saveConfigAs || null }),
    }),
  listScrapeRuns: () => request<ScrapeRun[]>("/scrape-runs"),
  getScrapeRun: (id: string) => request<ScrapeRun>(`/scrape-runs/${id}`),
};
