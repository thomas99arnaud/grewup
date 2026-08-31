from backend.modules.applications.dossier import compact_rows, load_dossier


def test_compact_merges_generic_courses_under_parent():
    text = compact_rows(
        [
            (
                "Classes préparatoires PCSI-PSI\nContexte : deux ans.",
                "2020-2022 | Nîmes | Lycée Daudet",
            ),
            ("Mathématiques", "Cours, TD, colles, DS"),
            ("Analyse (fonctions, suites, séries)", "Cours, TD, colles, DS"),
            ("Physique", "Cours, TD"),
            (
                "TIPE avalanches\nContexte : modélisation du risque.",
                "2021-2022 | Super Dévoluy",
            ),
            (
                "Développement d'algorithmes de pentes à risque selon un bulletin météo.",
                "Python",
            ),
        ]
    )
    assert "## Classes préparatoires PCSI-PSI" in text
    assert "Matières (ne pas lister une par une sur un CV) : Mathématiques ; Analyse ; Physique" in text
    assert "## Mathématiques" not in text
    assert "Développement d'algorithmes de pentes à risque" in text
    assert "Outils : Python" in text


def test_compact_keeps_project_rows():
    text = compact_rows(
        [
            (
                "Diplôme d'ingénieur en informatique (spécialité IA)",
                "2022-2025 | Lannion | ENSSAT",
            ),
            (
                "JAVA : théorie POO. Projet Quizz solo ou multijoueur.",
                "Java, Swing",
            ),
        ]
    )
    assert "Projet Quizz" in text
    assert "Java, Swing" in text
    assert "Matières" not in text


def test_load_suivi_word_is_compact():
    text = load_dossier()
    assert "outil de configuration industrielle" in text.lower() or "configuration industrielle" in text.lower()
    assert "janvier" in text.lower() or "2026" in text
    assert "Ministère des Transports" in text or "Ministère des transports" in text
    assert "## Mathématiques" not in text
    assert len(text) < 32000
