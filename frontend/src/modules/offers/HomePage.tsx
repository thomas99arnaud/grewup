import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, DashboardStats, Offer, ScrapeRun } from "../../shared/api";
import { ScrapeForm } from "./ScrapeForm";

export function HomePage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentOffers, setRecentOffers] = useState<Offer[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [dashboard, offers] = await Promise.all([
        api.dashboard(),
        api.listOffers(new URLSearchParams({ page: "1", page_size: "8" })),
      ]);
      setStats(dashboard);
      setRecentOffers(offers.items);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="home">
      <section className="hero">
        <h1>Offres VIE</h1>
        <p className="subtitle">
          Recherche les missions VIE sur Business France ou parcours tes offres sauvegardées.
        </p>
      </section>

      <section className="card scrape-card">
        <ScrapeForm onComplete={load} />
      </section>

      {error && <p className="msg error">{error}</p>}

      {stats && (
        <section className="stats-bar">
          <div className="stat">
            <span className="stat-n">{stats.total_offers}</span>
            <span className="stat-l">offres</span>
          </div>
          <div className="stat accent">
            <span className="stat-n">{stats.new_offers}</span>
            <span className="stat-l">nouvelles</span>
          </div>
          <div className="stat">
            <span className="stat-n">{stats.shortlisted_offers}</span>
            <span className="stat-l">shortlist</span>
          </div>
        </section>
      )}

      <section className="two-col">
        <div className="card">
          <div className="card-head">
            <h2>Dernières offres</h2>
            <Link to="/offers" className="link">
              Tout voir
            </Link>
          </div>
          {recentOffers.length === 0 ? (
            <p className="empty">Aucune offre pour l&apos;instant.</p>
          ) : (
            <ul className="offer-list">
              {recentOffers.map((offer) => (
                <li key={offer.id}>
                  <Link to={`/offers/${offer.id}`} className="offer-item">
                    <span className="offer-title">{offer.title}</span>
                    <span className="offer-meta">
                      {offer.company} · <span className={`tag source-${offer.source}`}>{offer.source}</span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <div className="card-head">
            <h2>Derniers scrapings</h2>
          </div>
          {!stats || stats.recent_runs.length === 0 ? (
            <p className="empty">Aucun scraping lancé.</p>
          ) : (
            <ul className="run-list">
              {stats.recent_runs.map((run: ScrapeRun) => (
                <li key={run.id} className="run-item">
                  <span className={`tag status-${run.status}`}>{run.status}</span>
                  <span className="run-detail">
                    {run.offers_new} nouvelle(s) / {run.offers_found} trouvée(s)
                  </span>
                  <span className="run-date">
                    {new Date(run.created_at).toLocaleDateString("fr-FR")}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </div>
  );
}
