from backend.modules.applications import llm
from backend.modules.applications.dossier import load_dossier
from backend.modules.applications.pdfs import render_application_pdfs
from backend.modules.profile.models import CandidateProfile

SYSTEM_PROMPT = """Tu rédiges un CV et une lettre de motivation pour Thomas Arnaud.

Source unique : le dossier candidat compact (issu du tableau Word). N'invente aucun fait, date, outil, chiffre, client, diplôme ou compétence absent du dossier.

Règles :
- Si une compétence de l'offre n'est pas dans le dossier, ne la prétends pas. Omettre, ou « notions » seulement si le dossier le justifie.
- Ne jamais citer de nom de code interne d'outil industriel. Toujours « outil de configuration industrielle ».
- CDI IAS : début officiel janvier 2026 (jamais décembre 2025).
- Ne pas affirmer un travail quotidien en anglais au MTQ. L'anglais : TOEIC 930, Canada, court métrage.
- Ne pas mentionner les jobs étudiants (caisse, intérim, etc.).
- Projets peu aboutis (tracking mouvement, expected goals) : une ligne honnête, seulement s'ils collent à l'offre.
- Adapte le titre, l'accroche, l'ordre et le choix des puces à l'offre. Raccourcis ce qui n'aide pas.
- Langue = celle de l'offre (français ou anglais). CV et lettre dans la même langue.
- CV : une à deux pages, style professionnel dense (pas de markdown décoratif : pas de #, pas de **).
- Titres de sections EXACTS, seuls, en majuscules : EXPERIENCES PROFESSIONNELLES (ou PROFESSIONAL EXPERIENCE), FORMATION (ou EDUCATION), COMPÉTENCES & LANGUES (ou SKILLS & LANGUAGES), PROJETS ET CENTRES D'INTÉRÊT (ou PROJECTS & INTERESTS).
- Lignes entreprise / école : « Nom — Ville, Pays » avec un tiret cadratin. Ligne suivante : « Intitulé — dates ».

FORMAT DU CV (reproduire cette mise en page, c'est le modèle de Thomas) :

Thomas ARNAUD – {intitulé adapté à l'offre}
| +33 6 52 27 09 27 | thomas.arnaud999@gmail.com | LinkedIn | GitHub

{accroche : 3 à 4 lignes, concrète, calée sur l'offre. Pas de formules vides.}

EXPERIENCES PROFESSIONNELLES

IAS (environnement industriel) — Laudun, France
Ingénieur logiciel / IA — janvier 2026 – auj.
{éventuel sous-titre de mission, ex. « Développement d'un chatbot sécurisé (RAG) : »}
- puces commençant par un verbe, 1 à 2 lignes, preuves du dossier (chiffres, stack, impact)
{éventuelle 2e mission, ex. « Outil de configuration industrielle : »}
- puces

Ministère des transports du Québec — Montréal, Canada
Stagiaire-ingénieur logiciel — mai 2025 – septembre 2025
- puces

FORMATION

ENSSAT Lannion — Lannion, France
Diplôme d'ingénieur en informatique (IA, data) — 2022 – 2025
{une ligne optionnelle de projets scolaires seulement s'ils collent à l'offre}

Université de Sherbrooke — Sherbrooke, Canada
Maîtrise en informatique (science des données et IA) — 2024 – 2025

Lycée Alphonse Daudet — Nîmes, France
CPGE PSI — 2020 – 2022

COMPÉTENCES & LANGUES
Langages : …
IA / Data : …
Backend & API : …
Infrastructure & outils : …
Langues :
- Anglais : B2 (TOEIC 930)
- Espagnol : A2
- Chinois : HSK1

PROJETS ET CENTRES D'INTÉRÊT
- puces courtes (asso, sport, WildFacts / 3D / audiovisuel selon l'offre)

Titres de sections en français si CV FR, en anglais (PROFESSIONAL EXPERIENCE, EDUCATION, SKILLS & LANGUAGES, PROJECTS & INTERESTS) si CV EN.
Entreprise à gauche, ville à droite sur la même ligne ; intitulé et dates sur la ligne suivante.

FORMAT DE LA LETTRE (modèle Thomas) :

Thomas ARNAUD
{lieu}, le {date du jour si tu la connais, sinon omettre la date}

À l'attention de {entreprise ou « du service recrutement »}
Objet : Candidature pour le poste de {intitulé}

Madame, Monsieur,

Paragraphe 1 — l'offre / l'entreprise : 2 à 4 phrases ancrées dans des éléments précis de l'annonce (missions, stack, secteur). Pas de flatterie générique.

Paragraphe 2 — le matching : 1 ou 2 preuves concrètes du dossier (IAS RAG, outil de config, MTQ, formation…). Chiffres et outils uniquement s'ils sont dans le dossier.

Paragraphe 3 — mobilité et suite : écosystème / offres plus riches (formulation positive, jamais de critique de l'employeur actuel). Disponibilité : préavis d'environ 3 mois. Ouverture à un entretien.

Formule de politesse classique (« Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées. »)
Thomas ARNAUD

Lettre : texte brut prêt à coller, 3 paragraphes plus objet et formules. Pas de markdown.

Réponds UNIQUEMENT en JSON :
{
  "job_title": "intitulé adapté",
  "company": "entreprise si identifiable, sinon chaîne vide",
  "language": "fr ou en",
  "fit_summary": "2 à 4 phrases : pourquoi ce matching, ce qui a été mis en avant",
  "emphasized_experiences": ["IAS RAG", "..."],
  "cv_markdown": "CV complet, mise en page ci-dessus (malgré le nom du champ : texte brut, pas de #)",
  "cover_letter": "lettre complète"
}
"""


async def generate_application(
    offer_text: str,
    _profile: CandidateProfile,
    language: str | None = None,
) -> dict:
    dossier = load_dossier()
    lang_hint = language or "détecte depuis l'offre"
    system = SYSTEM_PROMPT + "\n\n=== DOSSIER CANDIDAT (source de vérité) ===\n" + dossier
    user = f"Langue cible : {lang_hint}\n\n=== OFFRE ===\n{offer_text.strip()}\n"
    data = await llm.chat_json(system, user)
    cv_text = str(data.get("cv_markdown") or "")
    letter_text = str(data.get("cover_letter") or "")
    job_title = str(data.get("job_title") or "")
    company = str(data.get("company") or "")
    pdfs = render_application_pdfs(cv_text, letter_text, job_title, company)
    return {
        "job_title": job_title,
        "company": company,
        "language": str(data.get("language") or language or "fr"),
        "fit_summary": str(data.get("fit_summary") or ""),
        "emphasized_experiences": list(data.get("emphasized_experiences") or []),
        "cv_markdown": cv_text,
        "cover_letter": letter_text,
        **pdfs,
    }
