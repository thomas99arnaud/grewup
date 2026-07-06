import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, Offer, OfferSource, OfferStatus } from "../../shared/api";

const SOURCES: OfferSource[] = ["wttj", "indeed", "greenhouse", "lever", "manual"];
const STATUSES: OfferStatus[] = ["new", "reviewed", "shortlisted"];

export function OffersListPage() {
  const [offers, setOffers] = useState<Offer[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [source, setSource] = useState<OfferSource | "">("");
  const [status, setStatus] = useState<OfferStatus | "">("");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      if (source) params.set("source", source);
      if (status) params.set("status", status);
      if (search) params.set("search", search);
      const data = await api.listOffers(params);
      setOffers(data.items);
      setTotal(data.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }, [page, source, status, search]);

  useEffect(() => {
    load();
  }, [load]);

  const updateStatus = async (id: string, newStatus: OfferStatus) => {
    await api.updateOffer(id, { status: newStatus });
    load();
  };

  const totalPages = Math.ceil(total / 20) || 1;

  return (
    <div>
      <h2>Offres ({total})</h2>

      <div className="filters">
        <input
          type="search"
          placeholder="Rechercher..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (setSearch(searchInput), setPage(1))}
        />
        <button onClick={() => { setSearch(searchInput); setPage(1); }}>Filtrer</button>
        <select value={source} onChange={(e) => { setSource(e.target.value as OfferSource | ""); setPage(1); }}>
          <option value="">Toutes sources</option>
          {SOURCES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select value={status} onChange={(e) => { setStatus(e.target.value as OfferStatus | ""); setPage(1); }}>
          <option value="">Tous statuts</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {error && <p className="error">{error}</p>}
      {loading ? (
        <p>Chargement...</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Titre</th>
              <th>Entreprise</th>
              <th>Source</th>
              <th>Lieu</th>
              <th>Statut</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {offers.map((offer) => (
              <tr key={offer.id}>
                <td>
                  <Link to={`/offers/${offer.id}`}>{offer.title}</Link>
                </td>
                <td>{offer.company}</td>
                <td>
                  <span className={`badge source-${offer.source}`}>{offer.source}</span>
                </td>
                <td>{offer.location || "—"}</td>
                <td>
                  <span className={`badge status-${offer.status}`}>{offer.status}</span>
                </td>
                <td>{new Date(offer.scraped_at).toLocaleDateString("fr-FR")}</td>
                <td className="actions">
                  {offer.status !== "shortlisted" && (
                    <button onClick={() => updateStatus(offer.id, "shortlisted")}>★</button>
                  )}
                  <a href={offer.url} target="_blank" rel="noreferrer">↗</a>
                </td>
              </tr>
            ))}
            {offers.length === 0 && (
              <tr>
                <td colSpan={7}>Aucune offre</td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      <div className="pagination">
        <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Préc.</button>
        <span>Page {page} / {totalPages}</span>
        <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Suiv.</button>
      </div>
    </div>
  );
}
