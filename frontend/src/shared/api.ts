export type OfferSource = "vie" | "manual";
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
  specialization_ids: string[];
  teletravail: string[];
  porte_env: string[];
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


export type SkillLevel = "beginner" | "intermediate" | "advanced" | "expert";
export type LanguageLevel = "basic" | "intermediate" | "fluent" | "bilingual" | "native";

export interface Skill {
  id: string;
  profile_id: string;
  name: string;
  category: string | null;
  level: SkillLevel;
  years: number | null;
  description: string | null;
  sort_order: number;
}

export interface Language {
  id: string;
  profile_id: string;
  name: string;
  level: LanguageLevel;
  sort_order: number;
}

export interface Experience {
  id: string;
  profile_id: string;
  title: string;
  company: string;
  location: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  description: string;
  sort_order: number;
}

export interface Education {
  id: string;
  profile_id: string;
  degree: string;
  institution: string;
  field_of_study: string | null;
  location: string | null;
  start_date: string | null;
  end_date: string | null;
  description: string;
  sort_order: number;
}

export interface CandidateProfile {
  id: string;
  full_name: string;
  headline: string;
  summary: string;
  email: string | null;
  phone: string | null;
  location: string | null;
  linkedin_url: string | null;
  skills: Skill[];
  languages: Language[];
  experiences: Experience[];
  educations: Education[];
  created_at: string;
  updated_at: string;
}

export type ProfileUpdate = Pick<
  CandidateProfile,
  "full_name" | "headline" | "summary" | "email" | "phone" | "location" | "linkedin_url"
>;

export type SkillInput = Omit<Skill, "id" | "profile_id">;
export type LanguageInput = Omit<Language, "id" | "profile_id">;
export type ExperienceInput = Omit<Experience, "id" | "profile_id">;
export type EducationInput = Omit<Education, "id" | "profile_id">;

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
  getProfile: () => request<CandidateProfile>("/profile"),
  updateProfile: (data: ProfileUpdate) =>
    request<CandidateProfile>("/profile", { method: "PUT", body: JSON.stringify(data) }),
  createSkill: (data: SkillInput) =>
    request<Skill>("/profile/skills", { method: "POST", body: JSON.stringify(data) }),
  updateSkill: (id: string, data: Partial<SkillInput>) =>
    request<Skill>(`/profile/skills/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteSkill: (id: string) =>
    request<void>(`/profile/skills/${id}`, { method: "DELETE" }),
  createLanguage: (data: LanguageInput) =>
    request<Language>("/profile/languages", { method: "POST", body: JSON.stringify(data) }),
  deleteLanguage: (id: string) =>
    request<void>(`/profile/languages/${id}`, { method: "DELETE" }),
  createExperience: (data: ExperienceInput) =>
    request<Experience>("/profile/experiences", { method: "POST", body: JSON.stringify(data) }),
  updateExperience: (id: string, data: Partial<ExperienceInput>) =>
    request<Experience>(`/profile/experiences/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteExperience: (id: string) =>
    request<void>(`/profile/experiences/${id}`, { method: "DELETE" }),
  createEducation: (data: EducationInput) =>
    request<Education>("/profile/educations", { method: "POST", body: JSON.stringify(data) }),
  deleteEducation: (id: string) =>
    request<void>(`/profile/educations/${id}`, { method: "DELETE" }),
};
