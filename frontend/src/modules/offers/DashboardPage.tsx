import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, DashboardStats, ScrapeRun } from "../../shared/api";

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.dashboard().then(setStats).catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!stats) return <p>Chargement...</p>;

  return (
    <div>
      <h2>Dashboard</h2>
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-value">{stats.total_offers}</span>
          <span className="stat-label">Total offres</span>
        </div>
        <div className="stat-card highlight">
          <span className="stat-value">{stats.new_offers}</span>
          <span className="stat-label">Nouvelles</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{stats.shortlisted_offers}</span>
          <span className="stat-label">Shortlistées</span>
        </div>
      </div>

      <h3>Par source</h3>
      <ul className="source-list">
        {Object.entries(stats.by_source).map(([source, count]) => (
          <li key={source}>
            <span className={`badge source-${source}`}>{source}</span> {String(count)}
          </li>
        ))}
        {Object.keys(stats.by_source).length === 0 && <li>Aucune offre</li>}
      </ul>

      <h3>Derniers scrapings</h3>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Statut</th>
            <th>Trouvées</th>
            <th>Nouvelles</th>
            <th>Doublons</th>
          </tr>
        </thead>
        <tbody>
          {stats.recent_runs.map((run: ScrapeRun) => (
            <tr key={run.id}>
              <td>{new Date(run.created_at).toLocaleString("fr-FR")}</td>
              <td>
                <span className={`badge status-${run.status}`}>{run.status}</span>
              </td>
              <td>{run.offers_found}</td>
              <td>{run.offers_new}</td>
              <td>{run.offers_duplicates}</td>
            </tr>
          ))}
          {stats.recent_runs.length === 0 && (
            <tr>
              <td colSpan={5}>Aucun scraping</td>
            </tr>
          )}
        </tbody>
      </table>
      <p>
        <Link to="/scrape">Lancer un scraping</Link>
      </p>
    </div>
  );
}
