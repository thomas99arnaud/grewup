from backend.modules.applications.signature import (
    BLOCK_IAS_CONFIG,
    BLOCK_IAS_RAG,
    BLOCK_MTQ,
    adapt_cv,
    cv_signature,
    select_blocks,
)

RAG_OFFER = """
Ingénieur IA — chatbot RAG
Missions : concevoir un chatbot RAG sécurisé, LLM, LangChain,
déploiement GPU, documentation technique.
"""

DATA_OFFER = """
Data scientist transport / mobilité
Reconstitution d'itinéraires, enquêtes OD, OSRM, graphe routier,
modélisation des déplacements cyclistes.
"""

DOTNET_OFFER = """
Ingénieur logiciel C# .NET
Outil de configuration industrielle, versioning, environnement MES,
backend ASP.NET, IIS, Active Directory.
"""

HYBRID_OFFER = """
Ingénieur IA industrielle
Chatbot RAG et LLM, backend C# .NET en environnement industriel,
data scientist transport et mobilité, enquêtes OD.
"""


def test_signature_rag_keeps_ias_rag():
    assert select_blocks(RAG_OFFER) == [BLOCK_IAS_RAG]
    assert cv_signature(RAG_OFFER, "fr") == "fr|ias_rag"


def test_signature_data_transport_keeps_mtq():
    assert select_blocks(DATA_OFFER) == [BLOCK_MTQ]
    assert cv_signature(DATA_OFFER, "fr") == "fr|mtq"


def test_signature_dotnet_industrial_keeps_config():
    assert select_blocks(DOTNET_OFFER) == [BLOCK_IAS_CONFIG]
    assert cv_signature(DOTNET_OFFER, "fr") == "fr|ias_config"


def test_signature_hybrid_keeps_several_blocks():
    blocks = select_blocks(HYBRID_OFFER)
    assert blocks == [BLOCK_IAS_RAG, BLOCK_IAS_CONFIG, BLOCK_MTQ]
    assert cv_signature(HYBRID_OFFER, "fr") == "fr|ias_rag+ias_config+mtq"


def test_adapt_cv_retitles_and_reorders_skills():
    cv = """Thomas ARNAUD – Ancien titre
| +33 6 52 27 09 27 |  thomas.arnaud999@gmail.com

COMPÉTENCES & LANGUES
Langages : C, SQL, Python, C#
IA / Data : LangChain, traitement de données, RAG
"""
    out = adapt_cv(cv, "Ingénieur Python RAG", "Python RAG Docker LangChain")
    assert out.splitlines()[0] == "Thomas ARNAUD – Ingénieur Python RAG"
    langs = [ln for ln in out.splitlines() if ln.startswith("Langages")][0]
    assert langs.startswith("Langages : Python")
    ia = [ln for ln in out.splitlines() if ln.startswith("IA")][0]
    assert ia.index("RAG") < ia.index("traitement")
