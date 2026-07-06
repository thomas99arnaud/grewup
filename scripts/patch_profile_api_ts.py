from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

api_path = ROOT / "frontend/src/shared/api.ts"
api = api_path.read_text(encoding="utf-8")

start = api.find("\nexport type SkillLevel")
end = api.find("\nconst BASE =")
profile_api_end = api.find("  deleteExperience:")

new_profile_types = '''
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
'''

new_api_methods = '''  createSkill: (data: SkillInput) =>
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
    request<void>(`/profile/educations/${id}`, { method: "DELETE" }),'''

if start != -1 and end != -1:
    api = api[:start] + new_profile_types + api[end:]
    old_methods = api[api.find("  createSkill:"):api.find("};")]
    api = api.replace(old_methods, new_api_methods + "\n")
    api_path.write_text(api, encoding="utf-8", newline="\n")
    print("api.ts updated")
