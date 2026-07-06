from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

api_ts = (ROOT / "frontend/src/shared/api.ts").read_text(encoding="utf-8")

profile_block = '''
export type SkillLevel = "beginner" | "intermediate" | "advanced" | "expert";

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

export interface CandidateProfile {
  id: string;
  full_name: string;
  headline: string;
  summary: string;
  email: string | null;
  phone: string | null;
  location: string | null;
  linkedin_url: string | null;
  languages: string[];
  skills: Skill[];
  experiences: Experience[];
  created_at: string;
  updated_at: string;
}

export type ProfileUpdate = Pick<
  CandidateProfile,
  "full_name" | "headline" | "summary" | "email" | "phone" | "location" | "linkedin_url" | "languages"
>;

export type SkillInput = Omit<Skill, "id" | "profile_id">;
export type ExperienceInput = Omit<Experience, "id" | "profile_id">;
'''

if "export interface CandidateProfile" not in api_ts:
    api_ts = api_ts.replace(
        "const BASE = \"/api\";",
        profile_block + "\nconst BASE = \"/api\";",
    )

if "getProfile:" not in api_ts:
    api_ts = api_ts.replace(
        "  getScrapeRun: (id: string) => request<ScrapeRun>(`/scrape-runs/${id}`),\n};",
        """  getScrapeRun: (id: string) => request<ScrapeRun>(`/scrape-runs/${id}`),
  getProfile: () => request<CandidateProfile>("/profile"),
  updateProfile: (data: ProfileUpdate) =>
    request<CandidateProfile>("/profile", { method: "PUT", body: JSON.stringify(data) }),
  createSkill: (data: SkillInput) =>
    request<Skill>("/profile/skills", { method: "POST", body: JSON.stringify(data) }),
  updateSkill: (id: string, data: Partial<SkillInput>) =>
    request<Skill>(`/profile/skills/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteSkill: (id: string) =>
    request<void>(`/profile/skills/${id}`, { method: "DELETE" }),
  createExperience: (data: ExperienceInput) =>
    request<Experience>("/profile/experiences", { method: "POST", body: JSON.stringify(data) }),
  updateExperience: (id: string, data: Partial<ExperienceInput>) =>
    request<Experience>(`/profile/experiences/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteExperience: (id: string) =>
    request<void>(`/profile/experiences/${id}`, { method: "DELETE" }),
};""",
    )

(ROOT / "frontend/src/shared/api.ts").write_text(api_ts, encoding="utf-8", newline="\n")

profile_page = r'''import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  api,
  CandidateProfile,
  Experience,
  ExperienceInput,
  ProfileUpdate,
  Skill,
  SkillInput,
  SkillLevel,
} from "../../shared/api";

type Tab = "general" | "skills" | "experiences";

const LEVELS: { value: SkillLevel; label: string }[] = [
  { value: "beginner", label: "Débutant" },
  { value: "intermediate", label: "Intermédiaire" },
  { value: "advanced", label: "Avancé" },
  { value: "expert", label: "Expert" },
];

const emptySkill = (): SkillInput => ({
  name: "",
  category: "",
  level: "intermediate",
  years: null,
  description: "",
  sort_order: 0,
});

const emptyExperience = (): ExperienceInput => ({
  title: "",
  company: "",
  location: "",
  start_date: null,
  end_date: null,
  is_current: false,
  description: "",
  sort_order: 0,
});

export function ProfilePage() {
  const [tab, setTab] = useState<Tab>("general");
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [form, setForm] = useState<ProfileUpdate | null>(null);
  const [languagesInput, setLanguagesInput] = useState("");
  const [skillForm, setSkillForm] = useState<SkillInput>(emptySkill());
  const [expForm, setExpForm] = useState<ExperienceInput>(emptyExperience());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getProfile();
      setProfile(data);
      setForm({
        full_name: data.full_name,
        headline: data.headline,
        summary: data.summary,
        email: data.email,
        phone: data.phone,
        location: data.location,
        linkedin_url: data.linkedin_url,
        languages: data.languages || [],
      });
      setLanguagesInput((data.languages || []).join(", "));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const flash = (msg: string) => {
    setSuccess(msg);
    window.setTimeout(() => setSuccess(null), 2500);
  };

  const saveProfile = async (e: FormEvent) => {
    e.preventDefault();
    if (!form) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateProfile({
        ...form,
        languages: languagesInput
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      });
      setProfile(updated);
      flash("Profil enregistré");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSaving(false);
    }
  };

  const addSkill = async (e: FormEvent) => {
    e.preventDefault();
    if (!skillForm.name.trim()) return;
    setSaving(true);
    try {
      await api.createSkill({
        ...skillForm,
        name: skillForm.name.trim(),
        category: skillForm.category?.trim() || null,
        description: skillForm.description?.trim() || null,
      });
      setSkillForm(emptySkill());
      await load();
      flash("Compétence ajoutée");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSaving(false);
    }
  };

  const removeSkill = async (id: string) => {
    if (!confirm("Supprimer cette compétence ?")) return;
    await api.deleteSkill(id);
    await load();
  };

  const addExperience = async (e: FormEvent) => {
    e.preventDefault();
    if (!expForm.title.trim() || !expForm.company.trim()) return;
    setSaving(true);
    try {
      await api.createExperience({
        ...expForm,
        title: expForm.title.trim(),
        company: expForm.company.trim(),
        location: expForm.location?.trim() || null,
        end_date: expForm.is_current ? null : expForm.end_date,
      });
      setExpForm(emptyExperience());
      await load();
      flash("Expérience ajoutée");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSaving(false);
    }
  };

  const removeExperience = async (id: string) => {
    if (!confirm("Supprimer cette expérience ?")) return;
    await api.deleteExperience(id);
    await load();
  };

  if (loading) {
    return <p className="empty pad">Chargement du profil…</p>;
  }

  return (
    <div className="page profile-page">
      <div className="page-head">
        <div>
          <h1>Mon socle CV</h1>
          <p className="subtitle">
            Centralise tes compétences et expériences pour affiner la sélection d&apos;offres et préparer tes futurs CV.
          </p>
        </div>
        {profile && (
          <div className="profile-stats">
            <span>{profile.skills.length} compétence(s)</span>
            <span>{profile.experiences.length} expérience(s)</span>
          </div>
        )}
      </div>

      <div className="profile-tabs">
        {(
          [
            ["general", "Informations"],
            ["skills", "Compétences"],
            ["experiences", "Expériences"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={`profile-tab ${tab === id ? "active" : ""}`}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {error && <p className="msg error">{error}</p>}
      {success && <p className="msg success">{success}</p>}

      {tab === "general" && form && (
        <form className="card profile-section" onSubmit={saveProfile}>
          <div className="form-row">
            <label>
              Nom complet
              <input
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              />
            </label>
            <label>
              Titre / accroche
              <input
                value={form.headline}
                onChange={(e) => setForm({ ...form, headline: e.target.value })}
                placeholder="Ex. Ingénieur full-stack"
              />
            </label>
          </div>
          <label>
            Résumé
            <textarea
              rows={5}
              value={form.summary}
              onChange={(e) => setForm({ ...form, summary: e.target.value })}
              placeholder="Présentation courte de ton parcours et de tes objectifs"
            />
          </label>
          <div className="form-row">
            <label>
              Email
              <input
                type="email"
                value={form.email || ""}
                onChange={(e) => setForm({ ...form, email: e.target.value || null })}
              />
            </label>
            <label>
              Téléphone
              <input
                value={form.phone || ""}
                onChange={(e) => setForm({ ...form, phone: e.target.value || null })}
              />
            </label>
          </div>
          <div className="form-row">
            <label>
              Localisation
              <input
                value={form.location || ""}
                onChange={(e) => setForm({ ...form, location: e.target.value || null })}
              />
            </label>
            <label>
              LinkedIn
              <input
                value={form.linkedin_url || ""}
                onChange={(e) => setForm({ ...form, linkedin_url: e.target.value || null })}
                placeholder="https://linkedin.com/in/..."
              />
            </label>
          </div>
          <label>
            Langues (séparées par des virgules)
            <input
              value={languagesInput}
              onChange={(e) => setLanguagesInput(e.target.value)}
              placeholder="Français, Anglais, Espagnol"
            />
          </label>
          <button type="submit" className="btn primary" disabled={saving}>
            {saving ? "Enregistrement…" : "Enregistrer le profil"}
          </button>
        </form>
      )}

      {tab === "skills" && profile && (
        <div className="profile-stack">
          <form className="card profile-section" onSubmit={addSkill}>
            <h2>Ajouter une compétence</h2>
            <div className="form-row">
              <label>
                Compétence *
                <input
                  value={skillForm.name}
                  onChange={(e) => setSkillForm({ ...skillForm, name: e.target.value })}
                  placeholder="Python, gestion de projet…"
                />
              </label>
              <label>
                Catégorie
                <input
                  value={skillForm.category || ""}
                  onChange={(e) => setSkillForm({ ...skillForm, category: e.target.value })}
                  placeholder="Technique, soft skill…"
                />
              </label>
            </div>
            <div className="form-row">
              <label>
                Niveau
                <select
                  value={skillForm.level}
                  onChange={(e) =>
                    setSkillForm({ ...skillForm, level: e.target.value as SkillLevel })
                  }
                >
                  {LEVELS.map((l) => (
                    <option key={l.value} value={l.value}>
                      {l.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Années d&apos;expérience
                <input
                  type="number"
                  min={0}
                  value={skillForm.years ?? ""}
                  onChange={(e) =>
                    setSkillForm({
                      ...skillForm,
                      years: e.target.value ? Number(e.target.value) : null,
                    })
                  }
                />
              </label>
            </div>
            <button type="submit" className="btn primary" disabled={saving}>
              Ajouter
            </button>
          </form>

          <div className="card profile-section">
            <h2>Mes compétences ({profile.skills.length})</h2>
            {profile.skills.length === 0 ? (
              <p className="empty">Aucune compétence pour l&apos;instant.</p>
            ) : (
              <ul className="profile-list">
                {profile.skills.map((skill: Skill) => (
                  <li key={skill.id} className="profile-list-item">
                    <div>
                      <strong>{skill.name}</strong>
                      {skill.category && <span className="tag">{skill.category}</span>}
                      <span className="tag level">{LEVELS.find((l) => l.value === skill.level)?.label}</span>
                      {skill.years != null && (
                        <span className="col-muted"> · {skill.years} an(s)</span>
                      )}
                    </div>
                    <button
                      type="button"
                      className="icon-btn danger"
                      onClick={() => removeSkill(skill.id)}
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {tab === "experiences" && profile && (
        <div className="profile-stack">
          <form className="card profile-section" onSubmit={addExperience}>
            <h2>Ajouter une expérience</h2>
            <div className="form-row">
              <label>
                Poste *
                <input
                  value={expForm.title}
                  onChange={(e) => setExpForm({ ...expForm, title: e.target.value })}
                />
              </label>
              <label>
                Entreprise *
                <input
                  value={expForm.company}
                  onChange={(e) => setExpForm({ ...expForm, company: e.target.value })}
                />
              </label>
            </div>
            <div className="form-row">
              <label>
                Lieu
                <input
                  value={expForm.location || ""}
                  onChange={(e) => setExpForm({ ...expForm, location: e.target.value })}
                />
              </label>
              <label>
                Début
                <input
                  type="month"
                  value={expForm.start_date?.slice(0, 7) || ""}
                  onChange={(e) =>
                    setExpForm({
                      ...expForm,
                      start_date: e.target.value ? `${e.target.value}-01` : null,
                    })
                  }
                />
              </label>
              <label>
                Fin
                <input
                  type="month"
                  disabled={expForm.is_current}
                  value={expForm.end_date?.slice(0, 7) || ""}
                  onChange={(e) =>
                    setExpForm({
                      ...expForm,
                      end_date: e.target.value ? `${e.target.value}-01` : null,
                    })
                  }
                />
              </label>
            </div>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={expForm.is_current}
                onChange={(e) => setExpForm({ ...expForm, is_current: e.target.checked })}
              />
              Poste actuel
            </label>
            <label>
              Description
              <textarea
                rows={4}
                value={expForm.description}
                onChange={(e) => setExpForm({ ...expForm, description: e.target.value })}
              />
            </label>
            <button type="submit" className="btn primary" disabled={saving}>
              Ajouter
            </button>
          </form>

          <div className="card profile-section">
            <h2>Mes expériences ({profile.experiences.length})</h2>
            {profile.experiences.length === 0 ? (
              <p className="empty">Aucune expérience pour l&apos;instant.</p>
            ) : (
              <ul className="profile-list experiences">
                {profile.experiences.map((exp: Experience) => (
                  <li key={exp.id} className="profile-list-item column">
                    <div className="profile-exp-head">
                      <div>
                        <strong>{exp.title}</strong>
                        <span className="col-muted"> — {exp.company}</span>
                      </div>
                      <button
                        type="button"
                        className="icon-btn danger"
                        onClick={() => removeExperience(exp.id)}
                      >
                        ✕
                      </button>
                    </div>
                    <p className="col-muted small">
                      {exp.start_date?.slice(0, 7) || "?"} →{" "}
                      {exp.is_current ? "Aujourd'hui" : exp.end_date?.slice(0, 7) || "?"}
                      {exp.location ? ` · ${exp.location}` : ""}
                    </p>
                    {exp.description && <p className="profile-exp-desc">{exp.description}</p>}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
'''

main_ts = '''import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./shared/Layout";
import { HomePage } from "./modules/offers/HomePage";
import { OffersListPage } from "./modules/offers/OffersListPage";
import { OfferDetailPage } from "./modules/offers/OfferDetailPage";
import { AddOfferPage } from "./modules/offers/AddOfferPage";
import { ProfilePage } from "./modules/profile/ProfilePage";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="offers" element={<OffersListPage />} />
          <Route path="offers/add" element={<AddOfferPage />} />
          <Route path="offers/:id" element={<OfferDetailPage />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>
);
'''

layout_ts = '''import { Link, Outlet, useLocation } from "react-router-dom";

const nav = [
  { to: "/", label: "Accueil" },
  { to: "/offers", label: "Offres" },
  { to: "/profile", label: "Profil" },
  { to: "/offers/add", label: "Ajouter" },
];

export function Layout() {
  const { pathname } = useLocation();

  return (
    <div className="app">
      <header className="header">
        <Link to="/" className="brand">
          Grew
        </Link>
        <nav className="nav">
          {nav.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={
                pathname === item.to ||
                (item.to !== "/" && pathname.startsWith(item.to))
                  ? "active"
                  : ""
              }
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </header>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
'''

css_append = '''

/* Profile */
.profile-page .page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.profile-stats {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: var(--muted);
  white-space: nowrap;
}

.profile-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.profile-tab {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  cursor: pointer;
  font-size: 0.9rem;
}

.profile-tab.active {
  background: var(--accent-soft);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}

.profile-stack {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.profile-section h2 {
  margin: 0 0 1rem;
  font-size: 1rem;
}

.profile-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.profile-list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border);
}

.profile-list-item.column {
  flex-direction: column;
  align-items: stretch;
}

.profile-list-item:last-child {
  border-bottom: none;
}

.profile-exp-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.profile-exp-desc {
  margin: 0.5rem 0 0;
  font-size: 0.9rem;
  color: var(--text);
  white-space: pre-wrap;
}

.tag.level {
  background: var(--accent-soft);
  color: var(--accent);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.col-muted.small {
  font-size: 0.85rem;
  margin: 0.25rem 0 0;
}

.scrape-form select,
.profile-section select {
  width: 100%;
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  font: inherit;
  background: var(--surface);
}
'''

(ROOT / "frontend/src/modules/profile/ProfilePage.tsx").parent.mkdir(parents=True, exist_ok=True)
(ROOT / "frontend/src/modules/profile/ProfilePage.tsx").write_text(profile_page, encoding="utf-8", newline="\n")
(ROOT / "frontend/src/main.tsx").write_text(main_ts, encoding="utf-8", newline="\n")
(ROOT / "frontend/src/shared/Layout.tsx").write_text(layout_ts, encoding="utf-8", newline="\n")

css_path = ROOT / "frontend/src/index.css"
css = css_path.read_text(encoding="utf-8")
if ".profile-page" not in css:
    css_path.write_text(css + css_append, encoding="utf-8", newline="\n")

print("frontend profile done")
