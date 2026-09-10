import base64

from backend.modules.applications.pdfs import render_application_pdfs


SAMPLE_CV = """Thomas ARNAUD – Ingénieur logiciel / IA
| +33 6 52 27 09 27 |  thomas.arnaud999@gmail.com

Ingénieur logiciel spécialisé en IA appliquée, RAG et backend .NET. Expérience industrielle et internationale (Canada).

EXPERIENCES PROFESSIONNELLES

IAS (environnement industriel) — Laudun, France
Ingénieur logiciel / IA — janvier 2026 – auj.
Développement d'un chatbot sécurisé basé sur une architecture RAG :
- Conception d'une solution RAG en Python pour des milliers de documents.
- Déploiement auprès d'un acteur majeur de l'énergie.

Ministère des transports du Québec — Montréal, Canada
Stagiaire-ingénieur logiciel — mai 2025 – septembre 2025
- Application de reconstitution d'itinéraires cyclistes (OSRM, Streamlit).

FORMATION

ENSSAT Lannion — Lannion, France
Diplôme d'ingénieur en informatique (IA, data) — 2022 – 2025

Université de Sherbrooke — Sherbrooke, Canada
Maîtrise en informatique (science des données et IA) — 2024 – 2025

Lycée Alphonse Daudet — Nîmes, France
CPGE PSI — 2020 – 2022

COMPÉTENCES & LANGUES
Langages : Python, C#, SQL, C
IA / Data : RAG, LangChain, llama.cpp
Langues :
- Anglais : B2 (TOEIC 930)

PROJETS ET CENTRES D'INTÉRÊT
- WildFacts, Blender, football et handball
"""

SAMPLE_LETTER = """Thomas ARNAUD
Laudun-l'Ardoise

À l'attention du service recrutement
Objet : Candidature pour le poste d'ingénieur logiciel / IA

Madame, Monsieur,

Votre offre a retenu mon attention par son ancrage industriel et sa stack IA / backend.

Chez IAS, je conçois un chatbot RAG sécurisé utilisé par les métiers, ainsi qu'un outil de configuration industrielle.

Je suis mobile en France et à l'international, avec un préavis d'environ 3 mois. Je reste à votre disposition pour un entretien.

Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.
Thomas ARNAUD
"""


def test_render_two_pdfs():
    files = render_application_pdfs(SAMPLE_CV, SAMPLE_LETTER, "Ingénieur IA", "Exemple")
    cv = base64.b64decode(files["cv_pdf_base64"])
    letter = base64.b64decode(files["letter_pdf_base64"])
    assert cv.startswith(b"%PDF")
    assert letter.startswith(b"%PDF")
    assert files["cv_filename"].startswith("CV_Thomas_ARNAUD_")
    assert files["letter_filename"].startswith("LM_Thomas_ARNAUD_")
    assert files["cv_filename"].endswith(".pdf")
    assert b"Thomas" in cv or len(cv) > 800
    assert len(letter) > 800
    # Police du Word : Times New Roman si présente sur la machine
    assert b"Times" in cv
