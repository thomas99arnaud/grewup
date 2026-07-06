import { FormEvent, useEffect, useState } from "react";
import { api, ScrapeParams } from "../../shared/api";

interface ScrapeFormProps {
  onComplete?: () => void;
  compact?: boolean;
}

export function ScrapeForm({ onComplete, compact = false }: ScrapeFormProps) {
  const [keywords, setKeywords] = useState("");
  const [specializationId, setSpecializationId] = useState("24");
  const [maxResults, setMaxResults] = useState(30);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);

  useEffect(() => {
    if (!activeRunId) return;
    const interval = setInterval(async () => {
      try {
        const run = await api.getScrapeRun(activeRunId);
        if (run.status === "done") {
          setSuccess(`${run.offers_new} nouvelle(s) offre(s) ajoutée(s)`);
          setActiveRunId(null);
          setLoading(false);
          onComplete?.();
        } else if (run.status === "failed") {
          setError(run.error_message || "Échec du scraping");
          setActiveRunId(null);
          setLoading(false);
        }
      } catch {
        setActiveRunId(null);
        setLoading(false);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [activeRunId, onComplete]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
      setLoading(false);
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
          />
        </label>
        {!compact && (
          <label>
            Spécialisation (ID)
            <input
              value={specializationId}
              onChange={(e) => setSpecializationId(e.target.value)}
              placeholder="24"
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
          />
        </label>
      </div>

      {error && <p className="msg error">{error}</p>}
      {success && <p className="msg success">{success}</p>}

      <button type="submit" className="btn primary" disabled={loading}>
        {loading ? "Recherche en cours…" : "Lancer la recherche VIE"}
      </button>
    </form>
  );
}
