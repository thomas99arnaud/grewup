# Grew

Toolkit modulaire de préparation de candidatures : scraping d'offres, ajout manuel, suivi via interface web.

## Phase 1 — Module Offres

- Scraping multi-sources : Welcome to the Jungle, Indeed, Greenhouse, Lever
- Ajout manuel (URL ou collage)
- Base de données avec déduplication
- Interface web (dashboard, liste, détail, scraping)

## Prérequis

- Python 3.12+
- Node.js 20+
- Redis (optionnel, pour le worker ARQ)
- Playwright (pour Indeed)

## Installation

```bash
# Backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
playwright install chromium

# Frontend
cd frontend
npm install
```

Copier `.env.example` vers `.env` et ajuster si besoin.

Services optionnels (PostgreSQL + Redis) :

```bash
docker compose up -d
```

## Lancement

Terminal 1 — API :

```bash
uvicorn backend.main:app --reload --port 8000
```

Terminal 2 — Worker ARQ (optionnel, sinon scraping en arrière-plan intégré) :

```bash
arq backend.workers.scrape_worker.WorkerSettings
```

Terminal 3 — Frontend :

```bash
cd frontend && npm run dev
```

Ouvrir http://localhost:5173

## API

Documentation interactive : http://localhost:8000/docs

Endpoints principaux :

| Route | Description |
|-------|-------------|
| `GET /api/offers` | Liste des offres |
| `POST /api/offers/manual` | Création manuelle |
| `POST /api/offers/import-url` | Import depuis URL |
| `POST /api/scrape-runs` | Lancer un scraping |
| `GET /api/dashboard` | Statistiques |

## Architecture

```
backend/
  core/           # Config, events, registry modules
  modules/offers/ # Module Offres (Phase 1)
  workers/        # Jobs ARQ
frontend/
  src/modules/offers/  # Pages UI
```

Les modules futurs (profil, scoring, génération CV/LM) s'ajoutent dans `backend/modules/` et `frontend/src/modules/`.

## Génération CV / lettre

Page **CV / lettre** (`/apply`) : coller le texte d'une offre. Grew relit le Word de suivi (`backend/modules/applications/suivi-competences.docx`) à chaque génération, le compacte, appelle le LLM, puis **exporte deux PDF** (CV + lettre) au format Times / bleu des CV Word de Thomas.

Modifie ce `.docx` dans le projet : la génération suivante prend les changements, sans rebuild. Pour pointer vers un autre fichier :

```
CANDIDATE_DOSSIER_PATH=C:\Users\...\Suivi de compétences.docx
```

Dans `.env` :

```
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=anthropic/claude-sonnet-4.5
```

Compatible avec une API OpenAI (`OPENAI_BASE_URL` pour un proxy ou un modèle local). Le dossier compact est mis en cache prompt côté Claude (préfixe stable) : enchaîner plusieurs offres dans la même session coûte moins cher.

## Tests

```bash
pytest
```

## Notes

- **Indeed** : source fragile (anti-bot). Prévoir l'import manuel par URL en fallback.
- Scraping à usage personnel ; respecter les rate limits configurés dans `.env`.
