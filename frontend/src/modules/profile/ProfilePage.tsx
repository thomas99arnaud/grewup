import { FormEvent, ReactNode, useCallback, useEffect, useState } from "react";
import {
  api,
  CandidateProfile,
  Education,
  EducationInput,
  Experience,
  ExperienceInput,
  Language,
  LanguageInput,
  LanguageLevel,
  ProfileUpdate,
  Skill,
  SkillInput,
  SkillLevel,
} from "../../shared/api";

const SKILL_LEVELS: { value: SkillLevel; label: string }[] = [
  { value: "beginner", label: "Débutant" },
  { value: "intermediate", label: "Intermédiaire" },
  { value: "advanced", label: "Avancé" },
  { value: "expert", label: "Expert" },
];

const LANG_LEVELS: { value: LanguageLevel; label: string }[] = [
  { value: "basic", label: "Notions" },
  { value: "intermediate", label: "Intermédiaire" },
  { value: "fluent", label: "Courant" },
  { value: "bilingual", label: "Bilingue" },
  { value: "native", label: "Langue maternelle" },
];

const SKILL_CATEGORY_SUGGESTIONS = [
  "Soft skills",
  "Management & leadership",
  "Communication",
  "Organisation",
  "Langages",
  "IA / Data",
  "Backend & API",
  "Infrastructure & Outils",
  "Technique",
  "Centres d'intérêt",
];

const SOFT_CATEGORY_RE =
  /soft|relation|management|leadership|communication|organisation|équipe|team|humain/i;

function isSoftSkill(category: string | null | undefined): boolean {
  return SOFT_CATEGORY_RE.test(category?.trim() || "");
}

function Section({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <section className="card profile-section">
      <h2 className="profile-section-title">{title}</h2>
      {hint && <p className="profile-section-hint">{hint}</p>}
      {children}
    </section>
  );
}

function fmtMonth(d: string | null) {
  return d?.slice(0, 7) || "?";
}

function SkillChips({
  skills,
  variant,
  onDelete,
}: {
  skills: Skill[];
  variant: "technical" | "soft";
  onDelete: (id: string) => void;
}) {
  if (skills.length === 0) {
    return <p className="empty">Aucune compétence dans cette catégorie.</p>;
  }

  return (
    <div className={`skill-chips skill-chips-${variant}`}>
      {skills.map((skill) => (
        <div key={skill.id} className={`skill-chip skill-chip-${variant}`}>
          <div className="skill-chip-body">
            <span className="skill-chip-name">{skill.name}</span>
            <span className="skill-chip-meta">
              {SKILL_LEVELS.find((l) => l.value === skill.level)?.label}
              {skill.years != null ? ` · ${skill.years} an(s)` : ""}
            </span>
            {skill.description && <p className="skill-chip-desc">{skill.description}</p>}
          </div>
          <button
            type="button"
            className="skill-chip-remove"
            title="Supprimer"
            onClick={() => onDelete(skill.id)}
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}

function SkillsByCategory({
  skills,
  onDelete,
}: {
  skills: Skill[];
  onDelete: (id: string) => void;
}) {
  const byCategory = skills.reduce<Record<string, Skill[]>>((acc, s) => {
    const cat = s.category?.trim() || "Autre";
    (acc[cat] ||= []).push(s);
    return acc;
  }, {});

  return (
    <>
      {Object.entries(byCategory).map(([category, items]) => (
        <div key={category} className="skill-group">
          <h3 className="skill-group-title">{category}</h3>
          <SkillChips skills={items} variant="technical" onDelete={onDelete} />
        </div>
      ))}
    </>
  );
}

export function ProfilePage() {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [form, setForm] = useState<ProfileUpdate | null>(null);
  const [skillForm, setSkillForm] = useState<SkillInput>({
    name: "",
    category: "Technique",
    level: "intermediate",
    years: null,
    description: "",
    sort_order: 0,
  });
  const [langForm, setLangForm] = useState<LanguageInput>({ name: "", level: "intermediate", sort_order: 0 });
  const [expForm, setExpForm] = useState<ExperienceInput>({
    title: "",
    company: "",
    location: "",
    start_date: null,
    end_date: null,
    is_current: false,
    description: "",
    sort_order: 0,
  });
  const [eduForm, setEduForm] = useState<EducationInput>({
    degree: "",
    institution: "",
    field_of_study: "",
    location: "",
    start_date: null,
    end_date: null,
    description: "",
    sort_order: 0,
  });
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
      });
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

  const deleteSkill = async (id: string) => {
    await api.deleteSkill(id);
    await load();
  };

  const saveIdentity = async (e: FormEvent) => {
    e.preventDefault();
    if (!form) return;
    setSaving(true);
    try {
      const updated = await api.updateProfile(form);
      setProfile(updated);
      flash("Coordonnées enregistrées");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSaving(false);
    }
  };

  const saveNotes = async (e: FormEvent) => {
    e.preventDefault();
    if (!form) return;
    setSaving(true);
    try {
      const updated = await api.updateProfile(form);
      setProfile(updated);
      flash("Notes enregistrées");
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
      setSkillForm({
        name: "",
        category: isSoftSkill(skillForm.category) ? "Soft skills" : "Technique",
        level: "intermediate",
        years: null,
        description: "",
        sort_order: 0,
      });
      await load();
      flash("Compétence ajoutée");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSaving(false);
    }
  };

  const addLanguage = async (e: FormEvent) => {
    e.preventDefault();
    if (!langForm.name.trim()) return;
    setSaving(true);
    try {
      await api.createLanguage({ ...langForm, name: langForm.name.trim() });
      setLangForm({ name: "", level: "intermediate", sort_order: 0 });
      await load();
      flash("Langue ajoutée");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSaving(false);
    }
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
      setExpForm({
        title: "",
        company: "",
        location: "",
        start_date: null,
        end_date: null,
        is_current: false,
        description: "",
        sort_order: 0,
      });
      await load();
      flash("Expérience ajoutée");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSaving(false);
    }
  };

  const addEducation = async (e: FormEvent) => {
    e.preventDefault();
    if (!eduForm.degree.trim() || !eduForm.institution.trim()) return;
    setSaving(true);
    try {
      await api.createEducation({
        ...eduForm,
        degree: eduForm.degree.trim(),
        institution: eduForm.institution.trim(),
        field_of_study: eduForm.field_of_study?.trim() || null,
        location: eduForm.location?.trim() || null,
      });
      setEduForm({
        degree: "",
        institution: "",
        field_of_study: "",
        location: "",
        start_date: null,
        end_date: null,
        description: "",
        sort_order: 0,
      });
      await load();
      flash("Formation ajoutée");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="empty pad">Chargement de ton profil…</p>;

  const allSkills = profile?.skills || [];
  const softSkills = allSkills.filter((s) => isSoftSkill(s.category));
  const technicalSkills = allSkills.filter((s) => !isSoftSkill(s.category));

  return (
    <div className="page profile-page">
      <div className="page-head">
        <div>
          <h1>Mon répertoire</h1>
          <p className="subtitle">
            Inventaire complet de tes compétences, expériences et formations — sans te figer sur un métier.
            Tu choisiras quoi mettre en avant lors de chaque candidature.
          </p>
        </div>
        {profile && (
          <div className="profile-stats">
            <span className="profile-stat">
              <strong>{technicalSkills.length}</strong> techniques
            </span>
            <span className="profile-stat">
              <strong>{softSkills.length}</strong> soft skills
            </span>
            <span className="profile-stat">
              <strong>{profile.languages.length}</strong> langues
            </span>
            <span className="profile-stat">
              <strong>{profile.experiences.length}</strong> expériences
            </span>
          </div>
        )}
      </div>

      {error && <p className="msg error">{error}</p>}
      {success && <p className="msg success">{success}</p>}

      {form && (
        <>
          <form onSubmit={saveIdentity}>
            <Section title="Coordonnées">
              <div className="form-row">
                <label>
                  Nom complet
                  <input
                    value={form.full_name}
                    onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  />
                </label>
                <label>
                  Email
                  <input
                    type="email"
                    value={form.email || ""}
                    onChange={(e) => setForm({ ...form, email: e.target.value || null })}
                  />
                </label>
              </div>
              <div className="form-row">
                <label>
                  Téléphone
                  <input
                    value={form.phone || ""}
                    onChange={(e) => setForm({ ...form, phone: e.target.value || null })}
                  />
                </label>
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
              <button type="submit" className="btn primary" disabled={saving}>
                {saving ? "Enregistrement…" : "Enregistrer les coordonnées"}
              </button>
            </Section>
          </form>

          <Section
            title="Compétences techniques"
            hint="Tout ce que tu sais faire concrètement : outils, langages, domaines — sans filtrer par métier cible."
          >
            {technicalSkills.length > 0 ? (
              <SkillsByCategory skills={technicalSkills} onDelete={deleteSkill} />
            ) : (
              <p className="empty">Aucune compétence technique renseignée.</p>
            )}
            <form className="profile-add-form" onSubmit={addSkill}>
              <div className="form-row">
                <input
                  value={skillForm.name}
                  onChange={(e) => setSkillForm({ ...skillForm, name: e.target.value })}
                  placeholder="Compétence *"
                />
                <input
                  list="skill-categories"
                  value={skillForm.category || ""}
                  onChange={(e) => setSkillForm({ ...skillForm, category: e.target.value })}
                  placeholder="Catégorie"
                />
                <datalist id="skill-categories">
                  {SKILL_CATEGORY_SUGGESTIONS.map((c) => (
                    <option key={c} value={c} />
                  ))}
                </datalist>
                <select
                  value={skillForm.level}
                  onChange={(e) => setSkillForm({ ...skillForm, level: e.target.value as SkillLevel })}
                >
                  {SKILL_LEVELS.map((l) => (
                    <option key={l.value} value={l.value}>
                      {l.label}
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  min={0}
                  value={skillForm.years ?? ""}
                  onChange={(e) =>
                    setSkillForm({ ...skillForm, years: e.target.value ? Number(e.target.value) : null })
                  }
                  placeholder="Années"
                />
              </div>
              <textarea
                rows={2}
                value={skillForm.description || ""}
                onChange={(e) => setSkillForm({ ...skillForm, description: e.target.value })}
                placeholder="Précision optionnelle (contexte, exemple…)"
              />
              <button type="submit" className="btn sm primary" disabled={saving}>
                Ajouter une compétence
              </button>
            </form>
          </Section>

          <Section
            title="Soft skills & qualités"
            hint="Relationnel, organisation, leadership, adaptabilité… utiles pour tous types de postes."
          >
            <SkillChips skills={softSkills} variant="soft" onDelete={deleteSkill} />
          </Section>

          <Section title="Langues">
            {profile && profile.languages.length > 0 ? (
              <ul className="profile-list">
                {profile.languages.map((lang: Language) => (
                  <li key={lang.id} className="profile-list-item">
                    <div>
                      <strong>{lang.name}</strong>
                      <span className="tag level">
                        {LANG_LEVELS.find((l) => l.value === lang.level)?.label}
                      </span>
                    </div>
                    <button
                      type="button"
                      className="icon-btn danger"
                      onClick={async () => {
                        await api.deleteLanguage(lang.id);
                        await load();
                      }}
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="empty">Aucune langue renseignée.</p>
            )}
            <form className="profile-inline-form" onSubmit={addLanguage}>
              <input
                value={langForm.name}
                onChange={(e) => setLangForm({ ...langForm, name: e.target.value })}
                placeholder="Français, Anglais…"
              />
              <select
                value={langForm.level}
                onChange={(e) => setLangForm({ ...langForm, level: e.target.value as LanguageLevel })}
              >
                {LANG_LEVELS.map((l) => (
                  <option key={l.value} value={l.value}>
                    {l.label}
                  </option>
                ))}
              </select>
              <button type="submit" className="btn sm primary" disabled={saving}>
                Ajouter
              </button>
            </form>
          </Section>

          <form onSubmit={saveNotes}>
            <Section
              title="Notes libres"
              hint="Idées, angles de présentation, secteurs qui t'intéressent… Pas besoin de te résumer en un titre."
            >
              <label>
                Ce que tu veux garder en tête
                <textarea
                  rows={5}
                  value={form.summary}
                  onChange={(e) => setForm({ ...form, summary: e.target.value })}
                  placeholder="Ex. ouvert à l'industrie, le public, le conseil… Ce qui te motive, tes forces générales."
                />
              </label>
              <details className="profile-optional">
                <summary>Titre pour un CV ciblé (optionnel)</summary>
                <p className="profile-optional-hint">
                  À utiliser seulement quand tu génères un CV pour une offre précise — pas besoin de le remplir ici.
                </p>
                <label>
                  Intitulé de poste / accroche
                  <input
                    value={form.headline}
                    onChange={(e) => setForm({ ...form, headline: e.target.value })}
                    placeholder="Ex. Chef de projet digital, Analyste données…"
                  />
                </label>
              </details>
              <button type="submit" className="btn primary" disabled={saving}>
                {saving ? "Enregistrement…" : "Enregistrer les notes"}
              </button>
            </Section>
          </form>
        </>
      )}

      <Section title="Expériences">
        {profile && profile.experiences.length > 0 ? (
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
                    onClick={async () => {
                      await api.deleteExperience(exp.id);
                      await load();
                    }}
                  >
                    ✕
                  </button>
                </div>
                <p className="col-muted small">
                  {fmtMonth(exp.start_date)} → {exp.is_current ? "Aujourd'hui" : fmtMonth(exp.end_date)}
                  {exp.location ? ` · ${exp.location}` : ""}
                </p>
                {exp.description && <p className="profile-exp-desc">{exp.description}</p>}
              </li>
            ))}
          </ul>
        ) : (
          <p className="empty">Aucune expérience renseignée.</p>
        )}
        <form className="profile-add-form" onSubmit={addExperience}>
          <div className="form-row">
            <input
              value={expForm.title}
              onChange={(e) => setExpForm({ ...expForm, title: e.target.value })}
              placeholder="Intitulé du poste *"
            />
            <input
              value={expForm.company}
              onChange={(e) => setExpForm({ ...expForm, company: e.target.value })}
              placeholder="Entreprise *"
            />
            <input
              value={expForm.location || ""}
              onChange={(e) => setExpForm({ ...expForm, location: e.target.value })}
              placeholder="Lieu"
            />
          </div>
          <div className="form-row">
            <label className="month-label">
              Début
              <input
                type="month"
                value={expForm.start_date?.slice(0, 7) || ""}
                onChange={(e) =>
                  setExpForm({ ...expForm, start_date: e.target.value ? `${e.target.value}-01` : null })
                }
              />
            </label>
            <label className="month-label">
              Fin
              <input
                type="month"
                disabled={expForm.is_current}
                value={expForm.end_date?.slice(0, 7) || ""}
                onChange={(e) =>
                  setExpForm({ ...expForm, end_date: e.target.value ? `${e.target.value}-01` : null })
                }
              />
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={expForm.is_current}
                onChange={(e) => setExpForm({ ...expForm, is_current: e.target.checked })}
              />
              Poste actuel
            </label>
          </div>
          <textarea
            rows={3}
            value={expForm.description}
            onChange={(e) => setExpForm({ ...expForm, description: e.target.value })}
            placeholder="Missions et réalisations"
          />
          <button type="submit" className="btn sm primary" disabled={saving}>
            Ajouter une expérience
          </button>
        </form>
      </Section>

      <Section title="Formations">
        {profile && profile.educations.length > 0 ? (
          <ul className="profile-list experiences">
            {profile.educations.map((edu: Education) => (
              <li key={edu.id} className="profile-list-item column">
                <div className="profile-exp-head">
                  <div>
                    <strong>{edu.degree}</strong>
                    <span className="col-muted"> — {edu.institution}</span>
                    {edu.field_of_study && <span className="col-muted"> ({edu.field_of_study})</span>}
                  </div>
                  <button
                    type="button"
                    className="icon-btn danger"
                    onClick={async () => {
                      await api.deleteEducation(edu.id);
                      await load();
                    }}
                  >
                    ✕
                  </button>
                </div>
                <p className="col-muted small">
                  {fmtMonth(edu.start_date)} → {fmtMonth(edu.end_date)}
                  {edu.location ? ` · ${edu.location}` : ""}
                </p>
                {edu.description && <p className="profile-exp-desc">{edu.description}</p>}
              </li>
            ))}
          </ul>
        ) : (
          <p className="empty">Aucune formation renseignée.</p>
        )}
        <form className="profile-add-form" onSubmit={addEducation}>
          <div className="form-row">
            <input
              value={eduForm.degree}
              onChange={(e) => setEduForm({ ...eduForm, degree: e.target.value })}
              placeholder="Diplôme *"
            />
            <input
              value={eduForm.institution}
              onChange={(e) => setEduForm({ ...eduForm, institution: e.target.value })}
              placeholder="Établissement *"
            />
            <input
              value={eduForm.field_of_study || ""}
              onChange={(e) => setEduForm({ ...eduForm, field_of_study: e.target.value })}
              placeholder="Domaine"
            />
          </div>
          <div className="form-row">
            <label className="month-label">
              Début
              <input
                type="month"
                value={eduForm.start_date?.slice(0, 7) || ""}
                onChange={(e) =>
                  setEduForm({ ...eduForm, start_date: e.target.value ? `${e.target.value}-01` : null })
                }
              />
            </label>
            <label className="month-label">
              Fin
              <input
                type="month"
                value={eduForm.end_date?.slice(0, 7) || ""}
                onChange={(e) =>
                  setEduForm({ ...eduForm, end_date: e.target.value ? `${e.target.value}-01` : null })
                }
              />
            </label>
            <input
              value={eduForm.location || ""}
              onChange={(e) => setEduForm({ ...eduForm, location: e.target.value })}
              placeholder="Lieu"
            />
          </div>
          <button type="submit" className="btn sm primary" disabled={saving}>
            Ajouter une formation
          </button>
        </form>
      </Section>
    </div>
  );
}
