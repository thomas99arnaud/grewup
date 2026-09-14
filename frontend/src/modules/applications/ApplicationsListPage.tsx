import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  api,
  ApplicationListItem,
  ApplicationStatus,
  APPLICATION_STATUS_LABELS,
} from "../../shared/api";

const STATUSES: ApplicationStatus[] = ["draft", "applied", "interview", "rejected", "hired"];

export function ApplicationsListPage() {
  const [items, setItems] = useState<ApplicationListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<ApplicationStatus | "">("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: "50" });
      if (status) params.set("status", status);
      const data = await api.listApplications(params);
      setItems(data.items);
      setTotal(data.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }, [page, status]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = Math.ceil(total / 50) || 1;

  return (
    <div className="page offers-page">
      <div className="page-head compact">
        <h1>Candidatures</h1>
        <span className="count">{total}</span>
      </div>
      <p className="subtitle">CV et lettres générés, avec le suivi du statut.</p>

      <div className="toolbar compact">
        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value as ApplicationStatus | "");
            setPage(1);
          }}
        >
          <option value="">Tous les statuts</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {APPLICATION_STATUS_LABELS[s]}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="msg error">{error}</p>}

      <div className="offers-table-wrap card flat">
        {loading ? (
          <p className="empty pad">Chargement…</p>
        ) : items.length === 0 ? (
          <p className="empty pad">
            Aucune candidature. Génère un CV depuis <Link to="/apply">CV / lettre</Link>.
          </p>
        ) : (
          <table className="offers-table">
            <thead>
              <tr>
                <th>Poste</th>
                <th>Entreprise</th>
                <th>Statut</th>
                <th>Gardé</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id}>
                  <td className="col-title">
                    <Link to={`/applications/${row.id}`}>{row.job_title || "Sans titre"}</Link>
                    {row.reused_from_id ? <span className="tag reused">réutilisé</span> : null}
                  </td>
                  <td className="col-company">{row.company || "—"}</td>
                  <td>
                    <span className={`tag status-${row.status}`}>
                      {APPLICATION_STATUS_LABELS[row.status]}
                    </span>
                  </td>
                  <td className="col-muted">
                    {row.emphasized_experiences.length
                      ? row.emphasized_experiences.join(" · ")
                      : "—"}
                  </td>
                  <td className="col-muted">
                    {new Date(row.created_at).toLocaleDateString("fr-FR", {
                      day: "2-digit",
                      month: "2-digit",
                    })}
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
