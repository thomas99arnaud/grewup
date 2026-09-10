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
- Adapte le titre, l'accroche et le CHOIX des expériences à l'offre. Le dossier est une mine, pas une checklist.
- Langue = celle de l'offre (français ou anglais). CV et lettre dans la même langue.
- CV : STRICTEMENT 1 à 2 pages. Si ça dépasse, couper encore. Ce n'est pas un rapport technique.

SÉLECTION DES EXPÉRIENCES (étape 1, obligatoire) :
Blocs possibles : « IAS RAG », « IAS outil de configuration industrielle », « MTQ », « asso », « projets perso ».
Règle par défaut : OMETTRE. N'inclus un bloc que s'il aide clairement CETTE offre (missions, stack, secteur, pays). Sinon il n'apparaît nulle part dans le CV ni la lettre.
- Tu n'es PAS obligé de mettre IAS, ni MTQ, ni les deux missions IAS.
- Une seule expérience bien choisie vaut mieux que trois hors-sujet.
- Mettre les 3 blocs pro (IAS RAG + config + MTQ) est presque toujours une erreur, sauf offre explicitement hybride (IA + industriel + data/transport).
- Offre data / transport / géo / mobilité → MTQ ; omettre souvent la config, et le RAG s'il n'apporte rien.
- Offre RAG / LLM / chatbot / IA générative → IAS RAG ; MTQ seulement si data / Python utile ; config souvent à omettre.
- Offre .NET / C# / industriel / versioning / MES → outil de config + backend C# ; RAG seulement s'il sert l'annonce.
- Offre Canada / VIE / international → MTQ + le bloc stack qui matche ; ne pas coller le reste « pour faire volume ».
- emphasized_experiences = blocs GARDÉS. omitted_experiences = blocs ÉCARTÉS (au moins un en général). fit_summary = gardé / omis et pourquoi (2 à 4 phrases).
- Chaque bloc gardé : 3 à 5 puces, 1 ligne, verbe + résultat. Interdit de recopier le dossier. Interdit : RRF, KV cache, nœuds LangGraph, listes d'adaptateurs.

ATS (parseurs RH : Workday, Taleo, SmartRecruiters, etc.) :
- Une seule colonne, texte linéaire de haut en bas. Pas de tableaux, colonnes, icônes, encadrés, en-têtes/pieds de page.
- Contact en clair juste sous le nom, dans le corps du CV (jamais seulement en footer).
- Titre = intitulé proche de l'offre, avec les mots de l'annonce UNIQUEMENT s'ils sont vrais dans le dossier.
- Recopie les mots-clés de l'offre qui existent DANS le dossier, à l'identique (Python, Docker, RAG, .NET…). Dans le titre, l'accroche, 2–3 puces et les compétences. N'invente aucun mot-clé.
- Dates en toutes lettres, jamais 01/2026 ni « auj. » : « janvier 2026 – aujourd'hui », « mai 2025 – septembre 2025 ».
- Sections aux noms standards ci-dessous, seuls sur leur ligne, en majuscules.
- Compétences : d'abord les mots de l'offre présents dans le dossier, puis le reste utile. 4 lignes max. Préfixe + liste (Langages : …).

DENSITÉ :
- Accroche : 2 phrases. Expertise + contexte. Interdit : « je cherche », « VIE », « candidature ».
- Contact : uniquement « | +33 6 52 27 09 27 |  thomas.arnaud999@gmail.com »
- Formation : école + diplôme + dates UNIQUEMENT. Aucun projet scolaire.
- Centres d'intérêt : 3 puces courtes, seulement si ça sert (asso / sport / perso). Pas de budget, pas SPV sauf offre pompier.
- Titres de sections EXACTS, seuls, en majuscules : EXPERIENCES PROFESSIONNELLES (ou PROFESSIONAL EXPERIENCE), FORMATION (ou EDUCATION), COMPÉTENCES & LANGUES (ou SKILLS & LANGUAGES), PROJETS ET CENTRES D'INTÉRÊT (ou PROJECTS & INTERESTS).
- Lignes entreprise / école : « Nom — Ville, Pays ». Ligne suivante : « Intitulé — dates ».

FORMAT DU CV — densité et structure (exemple d'une SÉLECTION : offre data / transport → MTQ seul, IAS omis) :

Thomas ARNAUD – {intitulé adapté, ex. Ingénieur data / logiciel}
| +33 6 52 27 09 27 |  thomas.arnaud999@gmail.com

Ingénieur logiciel avec une expérience data appliquée à la mobilité : reconstitution d'itinéraires, graphes routiers et industrialisation d'une application (Python, Docker). Contexte international (Canada).

EXPERIENCES PROFESSIONNELLES

Ministère des transports du Québec — Montréal, Canada
Stagiaire-ingénieur logiciel — mai 2025 – septembre 2025
- Application de reconstitution d'itinéraires cyclistes à partir d'enquêtes OD (OSRM, Streamlit).
- Pondération du graphe routier et scénarios d'aménagement.
- Pipeline CI/CD (Azure DevOps, Docker) et documentation technique (~60 pages).
- Formation des utilisateurs finaux, contexte international.

Si tu gardes IAS RAG (offre chatbot / LLM), n'ajoute QUE ce bloc, 3–5 puces, pas la config :
IAS (environnement industriel critique) — Laudun, France
Ingénieur logiciel / IA — janvier 2026 – aujourd'hui
- Conception d'une solution RAG en Python pour de la documentation technique confidentielle (milliers de documents).
- Déploiement auprès d'un acteur majeur du secteur de l'énergie.
- Optimisation GPU/CUDA et gestion du contexte pour plusieurs utilisateurs.
- Backend .NET C# et Active Directory (accès, données sensibles) — seulement si l'offre parle de .NET / sécu.

Si tu gardes l'outil de config (offre .NET / industriel), n'ajoute QUE ce bloc :
IAS (environnement industriel critique) — Laudun, France
Ingénieur logiciel — janvier 2026 – aujourd'hui
- Outil de configuration industrielle : versions logicielles et documentaires (~49 machines).
- Traçabilité des évolutions et génération automatique de documents.
- Recueil de besoins auprès des métiers ; backend C# / .NET si l'offre le demande.

Ne recopie pas plusieurs de ces exemples « pour remplir ». Titres EN si CV anglais.

FORMATION

ENSSAT Lannion — Lannion, France
Diplôme d'ingénieur en informatique (IA, data) — 2022 – 2025

Université de Sherbrooke — Sherbrooke, Canada
Maîtrise en informatique (science des données et IA) — 2024 – 2025

Lycée Alphonse Daudet — Nîmes, France
CPGE PSI — 2020 – 2022

COMPÉTENCES & LANGUES
(filtre et réordonne : mots de l'offre d'abord, uniquement s'ils sont dans le dossier)
Langages : Python, C#, SQL, C
IA / Data : RAG, LangChain, traitement de données
Backend & API : .NET, API REST
Infrastructure & Outils : Docker, Git, CI/CD, IIS
Langues :
- Anglais : B2 (TOEIC 930)
- Espagnol : A2
- Chinois : HSK1

PROJETS ET CENTRES D'INTÉRÊT
- Projets perso : automatisation vidéo, génération 3D (Blender)
- Association : organisation d'événements, budget, coordination
- Sport : football (D1), handball (régional), musculation, running

Garde cette densité uniquement sur les blocs retenus. Formation et intérêts restent, même si tu n'as gardé qu'une expérience.

LETTRE — priorité absolue : qu'elle ait l'air écrite par Thomas, pas par un modèle.

Voix : première personne, phrases de longueurs inégales, un détail vécu. On parle comme à un recruteur qu'on respecte, sans jargon RH. Le CV vend les outils ; la lettre vend la personne et l'envie.

Qualités humaines (uniquement si le dossier les porte, via une SCÈNE, jamais un adjectif nu) :
- Terrain avec des non-dev : métiers (électriciens, automaticiens, qualité), analystes transport, utilisateurs du RAG.
- Transmission : encadrement d'un alternant, formation des utilisateurs MTQ, soutien maths collège/lycée.
- Collectif : foot et hand en club depuis l'enfance, asso (BDE/BDS, événements, tournois).
- Autonomie : seul profil développement dans l'équipe transport au MTQ.
- Envie vraie : outils dont les gens se servent (pas une démo) ; si l'offre est ailleurs / internationale / plus ouverte, attirance pour ce contexte — jamais « je m'ennuie » ni critique d'IAS.

Interdit (ça sonne IA / lettre type) :
« Votre offre a retenu mon attention », « c'est avec un vif intérêt », « je me permets de », « fort de mon expérience », « je suis convaincu d'être un atout », « dynamique / passionné / motivé / rigoureux » sans scène, « n'hésitez pas », « je reste dans l'attente », liste de techno, recopier le CV.

Ne mets PAS par défaut le couple « écosystème plus riche + préavis 3 mois ». Mobilité / international : seulement si l'offre est ailleurs, VIE, Canada, ou clairement plus ouverte. Préavis (~3 mois) : une demi-phrase en fin, seulement si utile. Sinon, termine sur l'envie d'échanger sur le poste.

Enveloppe formelle (OK, c'est FR) ; le corps doit être vivant :

Thomas ARNAUD
{lieu}, le {date du jour si tu la connais, sinon omettre}

À l'attention de {entreprise ou du service recrutement}
Objet : Candidature pour le poste de {intitulé}

Madame, Monsieur,

Paragraphe 1 — l'envie : pourquoi CETTE mission / cette équipe te parle. Un élément précis de l'annonce (pas la stack entière). 3–5 phrases.

Paragraphe 2 — une scène humaine tirée d'un bloc GARDÉ (ou asso / sport / transmission si ça éclaire le poste). Qu'est-ce que tu as fait avec des gens, qu'est-ce que ça dit de toi. 1 preuve technique max, au service de la scène.

Paragraphe 3 — ce que tu veux construire là, et ouverture à un échange. Chaleureux, pas commercial.

Formule de politesse classique, puis Thomas ARNAUD.

Texte brut, 3 paragraphes, ~180–280 mots. Pas de markdown. Même langue que le CV. Si offre EN : même voix humaine, sans formules US (« I am excited to leverage »).

Réponds UNIQUEMENT en JSON :
{
  "job_title": "intitulé adapté",
  "company": "entreprise si identifiable, sinon chaîne vide",
  "language": "fr ou en",
  "fit_summary": "Gardé / omis et pourquoi, calé sur l'offre",
  "emphasized_experiences": ["blocs gardés, ex. MTQ"],
  "omitted_experiences": ["blocs écartés, ex. IAS RAG", "IAS outil de configuration industrielle"],
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
    user = (
        f"Langue cible : {lang_hint}\n\n"
        "Étape 1 — sélection : pour CETTE offre, quels blocs garder ? Quels blocs omettre ? "
        "Remplis emphasized_experiences, omitted_experiences et fit_summary AVANT d'écrire le CV. "
        "Si tu hésites, omets.\n"
        "Étape 2 — rédige le CV (blocs retenus, ATS) et une lettre HUMAINE : envie pour cette offre, "
        "une scène vécue, qualités par les faits. Interdit les formules toutes faites.\n\n"
        f"=== OFFRE ===\n{offer_text.strip()}\n"
    )
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
        "omitted_experiences": list(data.get("omitted_experiences") or []),
        "cv_markdown": cv_text,
        "cover_letter": letter_text,
        **pdfs,
    }
