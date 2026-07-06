import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, Offer, OfferSource, OfferStatus } from "../../shared/api";

const SOURCES: OfferSource[] = ["vie", "manual"];
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
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: "50" });
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

  const deleteOffer = async (id: string, title: string) => {
    if (!confirm(`Supprimer « ${title} » ?`)) return;
    setDeletingId(id);
    try {
      await api.archiveOffer(id);
      setOffers((prev) => prev.filter((o) => o.id !== id));
      setTotal((t) => Math.max(0, t - 1));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur lors de la suppression");
    } finally {
      setDeletingId(null);
    }
  };

  const totalPages = Math.ceil(total / 50) || 1;

  return (
    <div className="page offers-page">
      <div className="page-head compact">
        <h1>Offres</h1>
        <span className="count">{total}</span>
      </div>

      <div className="toolbar compact">
        <input
          type="search"
          className="search-input"
          placeholder="Rechercher…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              setSearch(searchInput);
              setPage(1);
            }
          }}
        />
        <select
          value={source}
          onChange={(e) => {
            setSource(e.target.value as OfferSource | "");
            setPage(1);
          }}
        >
          <option value="">Source</option>
          {SOURCES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value as OfferStatus | "");
            setPage(1);
          }}
        >
          <option value="">Statut</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <button
          className="btn sm"
          onClick={() => {
            setSearch(searchInput);
            setPage(1);
          }}
        >
          OK
        </button>
      </div>

      {error && <p className="msg error">{error}</p>}

      <div className="offers-table-wrap card flat">
        {loading ? (
          <p className="empty pad">Chargement…</p>
        ) : offers.length === 0 ? (
          <p className="empty pad">Aucune offre trouvée.</p>
        ) : (
          <table className="offers-table">
            <thead>
              <tr>
                <th>Titre</th>
                <th>Entreprise</th>
                <th>Source</th>
                <th>Lieu</th>
                <th>Date</th>
                <th>Statut</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {offers.map((offer) => (
                <tr key={offer.id} className={deletingId === offer.id ? "deleting" : ""}>
                  <td className="col-title">
                    <Link to={`/offers/${offer.id}`}>{offer.title}</Link>
                  </td>
                  <td className="col-company">{offer.company}</td>
                  <td>
                    <span className={`tag source-${offer.source}`}>{offer.source}</span>
                  </td>
                  <td className="col-muted">{offer.location || "—"}</td>
                  <td className="col-muted">
                    {new Date(offer.scraped_at).toLocaleDateString("fr-FR", {
                      day: "2-digit",
                      month: "2-digit",
                    })}
                  </td>
                  <td>
                    <span className={`tag status-${offer.status}`}>{offer.status}</span>
                  </td>
                  <td className="col-actions">
                    {offer.status !== "shortlisted" && (
                      <button
                        className="icon-btn"
                        title="Shortlist"
                        onClick={() => updateStatus(offer.id, "shortlisted")}
                      >
                        ★
                      </button>
                    )}
                    <a
                      className="icon-btn"
                      href={offer.url}
                      target="_blank"
                      rel="noreferrer"
                      title="Ouvrir l'annonce"
                    >
                      ↗
                    </a>
                    <button
                      className="icon-btn danger"
                      title="Supprimer"
                      disabled={deletingId === offer.id}
                      onClick={() => deleteOffer(offer.id, offer.title)}
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button className="btn sm ghost" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            ←
          </button>
          <span>
            {page} / {totalPages}
          </span>
          <button
            className="btn sm ghost"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            →
          </button>
        </div>
      )}
    </div>
  );
}
