import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, OfferSource, ScrapeParams, ScrapeRun } from "../../shared/api";

const ALL_SOURCES: OfferSource[] = ["wttj", "indeed", "greenhouse", "lever"];

export function ScrapePage() {
  const [sources, setSources] = useState<OfferSource[]>(["wttj", "greenhouse"]);
  const [keywords, setKeywords] = useState("python developer");
  const [location, setLocation] = useState("Paris");
  const [greenhouseSlugs, setGreenhouseSlugs] = useState("stripe,gitlab");
  const [leverSlugs, setLeverSlugs] = useState("");
  const [maxResults, setMaxResults] = useState(30);
  const [saveAs, setSaveAs] = useState("");
  const [runs, setRuns] = useState<ScrapeRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);

  const loadRuns = useCallback(async () => {
    try {
      const data = await api.listScrapeRuns();
      setRuns(data);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    loadRuns();
  }, [loadRuns]);

  useEffect(() => {
    if (!activeRunId) return;
    const interval = setInterval(async () => {
      try {
        const run = await api.getScrapeRun(activeRunId);
        setRuns((prev) => prev.map((r) => (r.id === run.id ? run : r)));
        if (run.status === "done" || run.status === "failed") {
          setActiveRunId(null);
          setLoading(false);
        }
      } catch {
        setActiveRunId(null);
        setLoading(false);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [activeRunId]);

  const toggleSource = (s: OfferSource) => {
    setSources((prev) =>
      prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]
    );
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (sources.length === 0) {
      setError("Sélectionnez au moins une source");
      return;
    }
    setLoading(true);
    setError(null);
    const params: ScrapeParams = {
      sources,
      keywords,
      location,
      greenhouse_slugs: greenhouseSlugs.split(",").map((s) => s.trim()).filter(Boolean),
      lever_slugs: leverSlugs.split(",").map((s) => s.trim()).filter(Boolean),
      max_results_per_source: maxResults,
    };
    try {
      const run = await api.createScrapeRun(params, saveAs || undefined);
      setActiveRunId(run.id);
      await loadRuns();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Scraping</h2>

      <form onSubmit={handleSubmit} className="form scrape-form">
        <fieldset>
          <legend>Sources</legend>
          {ALL_SOURCES.map((s) => (
            <label key={s} className="checkbox">
              <input
                type="checkbox"
                checked={sources.includes(s)}
                onChange={() => toggleSource(s)}
              />
              {s}
            </label>
          ))}
        </fieldset>

        <label>
          Mots-clés
          <input value={keywords} onChange={(e) => setKeywords(e.target.value)} />
        </label>
        <label>
          Lieu
          <input value={location} onChange={(e) => setLocation(e.target.value)} />
        </label>
        <label>
          Slugs Greenhouse (séparés par virgule)
          <input
            value={greenhouseSlugs}
            onChange={(e) => setGreenhouseSlugs(e.target.value)}
            placeholder="stripe,gitlab,notion"
          />
        </label>
        <label>
          Slugs Lever (séparés par virgule)
          <input
            value={leverSlugs}
            onChange={(e) => setLeverSlugs(e.target.value)}
            placeholder="netflix,spotify"
          />
        </label>
        <label>
          Max résultats par source
          <input
            type="number"
            min={1}
            max={100}
            value={maxResults}
            onChange={(e) => setMaxResults(Number(e.target.value))}
          />
        </label>
        <label>
          Sauvegarder la config sous (optionnel)
          <input value={saveAs} onChange={(e) => setSaveAs(e.target.value)} />
        </label>

        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? "Scraping en cours..." : "Lancer le scraping"}
        </button>
      </form>

      <h3>Historique</h3>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Statut</th>
            <th>Params</th>
            <th>Trouvées</th>
            <th>Nouvelles</th>
            <th>Doublons</th>
            <th>Erreur</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.id}>
              <td>{new Date(run.created_at).toLocaleString("fr-FR")}</td>
              <td>
                <span className={`badge status-${run.status}`}>{run.status}</span>
              </td>
              <td className="params-cell">
                {String(run.params.keywords ?? "—")}
                {" / "}
                {String(run.params.location ?? "—")}
              </td>
              <td>{run.offers_found}</td>
              <td className="highlight-cell">{run.offers_new}</td>
              <td>{run.offers_duplicates}</td>
              <td className="error-cell">{run.error_message || "—"}</td>
            </tr>
          ))}
          {runs.length === 0 && (
            <tr>
              <td colSpan={7}>Aucun run</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
