"""Seed the singleton profile from Thomas Arnaud's CV (FR content)."""
import asyncio
from datetime import date

from backend.db.session import async_session_factory, init_db
from backend.modules.profile.models import LanguageLevel, SkillLevel
from backend.modules.profile.service import ProfileService

IAS_RAG_DESC = """Développement d'un chatbot sécurisé basé sur une architecture RAG :
- Conception d'une solution RAG (Chunking → Embeddings → Vector Store → Retrieving → LLM) en Python pour l'exploitation de documentation technique confidentielle (milliers de documents PDF, Word).
- Déploiement de la solution auprès d'un acteur majeur du secteur de l'énergie.
- Mise en place de la gestion du contexte dynamique et optimisation des performances (GPU/CUDA, parallélisation) pour exploiter au mieux les capacités des machines (VRAM, CPU, GPU).
- Développement d'un backend .NET C# avec intégration Active Directory (gestion des accès, sécurisation des données sensibles).
- Force de proposition et de décision sur l'infrastructure physique et logicielle (IIS, .NET, API REST, LLM)."""

IAS_CONFIG_DESC = """Développement d'un outil de gestion de configuration et de versioning :
- Structuration et suivi des versions logicielles et documentaires (49 machines à suivre par version).
- Mise en place d'un système de traçabilité des évolutions, détection des anomalies, rédaction automatique de documents.
- Choix techniques et définition de l'infrastructure (.NET, API REST, PostgreSQL, Docker).
- Conduite d'une démarche de recueil des besoins auprès de multiples équipes d'automaticiens."""

MTQ_DESC = """- Développement d'une application de prédiction du trafic cyclable à partir de données réelles pour Montréal, Québec et Ottawa afin d'anticiper les impacts des futurs travaux et du vieillissement de la population.
- Implémentation d'un serveur Python, OSRM, affinage des poids du graphe routier en fonction des données réelles.
- Analyse, nettoyage et visualisation de données.
- Rédaction d'un document technique, formation et accompagnement des utilisateurs finaux.
- Travail dans un contexte international."""

SUMMARY = (
    "Ouvert à des postes variés (tech, data, conseil, industrie, public…). "
    "Forces : analyse, rigueur technique, travail en équipe, contextes internationaux. "
    "Expérience en environnement industriel critique et au Canada."
)

SOFT_SKILLS = [
    ("Gestion d'association", "Management & leadership", SkillLevel.ADVANCED, "Organisation d'événements, budget, coordination"),
    ("Organisation d'événements", "Organisation", SkillLevel.ADVANCED),
    ("Conduite de recueil de besoins", "Communication", SkillLevel.ADVANCED),
    ("Formation & accompagnement utilisateurs", "Communication", SkillLevel.ADVANCED),
    ("Travail en contexte international", "Soft skills", SkillLevel.ADVANCED),
    ("Esprit d'équipe", "Soft skills", SkillLevel.ADVANCED, "Football D1, handball régional, rugby"),
    ("Force de proposition", "Soft skills", SkillLevel.ADVANCED),
]

SKILLS = [
    ("Python", "Langages", SkillLevel.ADVANCED),
    ("C#", "Langages", SkillLevel.ADVANCED),
    ("SQL", "Langages", SkillLevel.ADVANCED),
    ("C", "Langages", SkillLevel.INTERMEDIATE),
    ("RAG", "IA / Data", SkillLevel.ADVANCED, "chunking, embeddings, vector store, retrieval, LLM"),
    ("Traitement et analyse de données", "IA / Data", SkillLevel.ADVANCED),
    ("Vision par ordinateur", "IA / Data", SkillLevel.INTERMEDIATE),
    ("Réseaux de neurones", "IA / Data", SkillLevel.ADVANCED),
    ("Évaluation de modèles", "IA / Data", SkillLevel.ADVANCED),
    (".NET", "Backend & API", SkillLevel.ADVANCED),
    ("API REST", "Backend & API", SkillLevel.ADVANCED),
    ("Docker", "Infrastructure & Outils", SkillLevel.ADVANCED),
    ("PostgreSQL", "Infrastructure & Outils", SkillLevel.ADVANCED),
    ("IIS", "Infrastructure & Outils", SkillLevel.INTERMEDIATE),
    ("Azure DevOps", "Infrastructure & Outils", SkillLevel.INTERMEDIATE),
    ("Git", "Infrastructure & Outils", SkillLevel.ADVANCED),
    ("CI/CD", "Infrastructure & Outils", SkillLevel.INTERMEDIATE),
]

LANGUAGES = [
    ("Anglais", LanguageLevel.FLUENT),  # B2, TOEIC 930
    ("Espagnol", LanguageLevel.BASIC),  # A2
    ("Chinois", LanguageLevel.BASIC),  # HSK1
]


async def main() -> None:
    await init_db()
    async with async_session_factory() as session:
        service = ProfileService(session)

        profile = await service.get_profile()

        # Clear existing nested data to avoid duplicates on re-run
        for skill in list(profile.skills):
            await service.delete_skill(skill.id)
        for lang in list(profile.languages):
            await service.delete_language(lang.id)
        for exp in list(profile.experiences):
            await service.delete_experience(exp.id)
        for edu in list(profile.educations):
            await service.delete_education(edu.id)

        await service.update_profile(
            {
                "full_name": "Thomas Arnaud",
                "headline": "",
                "summary": SUMMARY,
                "email": "thomas.arnaud999@gmail.com",
                "phone": "+33 6 52 27 09 27",
                "location": "Laudun, France",
                "linkedin_url": None,
            }
        )

        await service.create_experience(
            {
                "title": "Ingénieur Logiciel / IA",
                "company": "IAS GROUP",
                "location": "Laudun, France",
                "start_date": date(2025, 12, 1),
                "end_date": None,
                "is_current": True,
                "description": IAS_RAG_DESC + "\n\n" + IAS_CONFIG_DESC,
                "sort_order": 0,
            }
        )

        await service.create_experience(
            {
                "title": "Stagiaire-Ingénieur Logiciel",
                "company": "Ministère des transports du Québec",
                "location": "Montréal, Canada",
                "start_date": date(2025, 5, 1),
                "end_date": date(2025, 9, 30),
                "is_current": False,
                "description": MTQ_DESC,
                "sort_order": 1,
            }
        )

        await service.create_education(
            {
                "degree": "Diplôme d'ingénieur en informatique",
                "institution": "ENSSAT",
                "field_of_study": "Analyse de données, IA",
                "location": "Lannion, France",
                "start_date": date(2022, 9, 1),
                "end_date": date(2025, 6, 30),
                "description": "",
                "sort_order": 0,
            }
        )

        await service.create_education(
            {
                "degree": "Maîtrise en informatique — science des données et IA",
                "institution": "Université de Sherbrooke",
                "field_of_study": "Science des données, forage de données",
                "location": "Sherbrooke, Canada",
                "start_date": date(2024, 9, 1),
                "end_date": date(2025, 6, 30),
                "description": "",
                "sort_order": 1,
            }
        )

        await service.create_education(
            {
                "degree": "CPGE PSI",
                "institution": "Lycée Alphonse Daudet",
                "field_of_study": "Mathématiques, physique",
                "location": "Nîmes, France",
                "start_date": date(2020, 9, 1),
                "end_date": date(2022, 6, 30),
                "description": "",
                "sort_order": 2,
            }
        )

        for i, item in enumerate(SKILLS + SOFT_SKILLS):
            name, category, level = item[0], item[1], item[2]
            description = item[3] if len(item) > 3 else None
            await service.create_skill(
                {
                    "name": name,
                    "category": category,
                    "level": level,
                    "description": description,
                    "sort_order": i,
                }
            )

        for i, (name, level) in enumerate(LANGUAGES):
            await service.create_language({"name": name, "level": level, "sort_order": i})

        await session.commit()
        profile = await service.get_profile()
        print(f"Profil rempli : {profile.full_name}")
        print(f"  {len(profile.experiences)} expériences, {len(profile.educations)} formations")
        print(f"  {len(profile.skills)} compétences, {len(profile.languages)} langues")


if __name__ == "__main__":
    asyncio.run(main())
