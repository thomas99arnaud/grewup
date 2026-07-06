import { FormEvent, useEffect, useState } from "react";
import { api, ScrapeParams, ScrapeRunStatus } from "../../shared/api";

interface ScrapeFormProps {
  onComplete?: () => void;
  compact?: boolean;
}

const STATUS_LABELS: Record<ScrapeRunStatus, string> = {
  pending: "Préparation de la recherche…",
  running: "Récupération des offres VIE…",
  done: "Terminé",
  failed: "Échec",
};

export function ScrapeForm({ onComplete, compact = false }: ScrapeFormProps) {
  const [keywords, setKeywords] = useState("");
  const [specializationId, setSpecializationId] = useState("24");
  const [maxResults, setMaxResults] = useState(30);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [runStatus, setRunStatus] = useState<ScrapeRunStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);

  useEffect(() => {
    if (!loading) return;

    const tick = setInterval(() => {
      setProgress((current) => {
        if (current >= 92) return current;
        const step = current < 40 ? 3 : current < 70 ? 2 : 1;
        return Math.min(92, current + step);
      });
    }, 350);

    return () => clearInterval(tick);
  }, [loading]);

  useEffect(() => {
    if (!activeRunId) return;

    const poll = async () => {
      try {
        const run = await api.getScrapeRun(activeRunId);
        setRunStatus(run.status);

        if (run.status === "done") {
          setProgress(100);
          const { offers_found, offers_new, offers_duplicates } = run;
          if (offers_new > 0) {
            setSuccess(
              `${offers_new} nouvelle(s) offre(s) ajoutée(s) sur ${offers_found} trouvée(s)`
            );
          } else if (offers_found > 0) {
            setSuccess(
              `${offers_found} offre(s) trouvée(s), déjà toutes en base (${offers_duplicates} doublon(s))`
            );
          } else {
            setSuccess("Aucune offre trouvée pour cette recherche");
          }
          setActiveRunId(null);
          setLoading(false);
          setRunStatus(null);
          window.setTimeout(() => setProgress(0), 800);
          onComplete?.();
        } else if (run.status === "failed") {
          setProgress(0);
          setError(run.error_message || "Échec du scraping");
          setActiveRunId(null);
          setLoading(false);
          setRunStatus(null);
        } else if (run.status === "running" && run.offers_found > 0) {
          const ratio = Math.min(95, Math.round((run.offers_found / maxResults) * 100));
          setProgress((current) => Math.max(current, ratio));
        }
      } catch {
        setProgress(0);
        setActiveRunId(null);
        setLoading(false);
        setRunStatus(null);
      }
    };

    poll();
    const interval = setInterval(poll, 1500);
    return () => clearInterval(interval);
  }, [activeRunId, maxResults, onComplete]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setProgress(8);
    setRunStatus("pending");
    setError(null);
    setSuccess(null);

    const params: ScrapeParams = {
      sources: ["vie"],
      keywords,
      specialization_ids: [specializationId],
      teletravail: ["0"],
      porte_env: ["0"],
      max_results_per_source: maxResults,
    };

    try {
      const run = await api.createScrapeRun(params);
      setActiveRunId(run.id);
      setRunStatus(run.status);
      setProgress(18);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
      setLoading(false);
      setProgress(0);
      setRunStatus(null);
    }
  };

  return (
    <form onSubmit={handleSubmit} className={`scrape-form ${compact ? "compact" : ""}`}>
      <p className="scrape-source-label">
        Source : <strong>Business France VIE</strong>
      </p>

      <div className="form-row">
        <label>
          Mots-clés
          <input
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            placeholder="Optionnel"
            disabled={loading}
          />
        </label>
        {!compact && (
          <label>
            Spécialisation (ID)
            <input
              value={specializationId}
              onChange={(e) => setSpecializationId(e.target.value)}
              placeholder="24"
              disabled={loading}
            />
          </label>
        )}
        <label>
          Max résultats
          <input
            type="number"
            min={1}
            max={100}
            value={maxResults}
            onChange={(e) => setMaxResults(Number(e.target.value))}
            disabled={loading}
          />
        </label>
      </div>

      {loading && (
        <div className="scrape-progress" role="status" aria-live="polite">
          <div className="scrape-progress-header">
            <span>{runStatus ? STATUS_LABELS[runStatus] : "Recherche en cours…"}</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="scrape-progress-track">
            <div className="scrape-progress-bar" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}

      {error && <p className="msg error">{error}</p>}
      {success && <p className="msg success">{success}</p>}

      <button type="submit" className="btn primary" disabled={loading}>
        {loading ? "Recherche en cours…" : "Lancer la recherche VIE"}
      </button>
    </form>
  );
}
