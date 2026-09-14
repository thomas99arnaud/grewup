import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApplicationListItem, Offer, OfferStatus } from "../../shared/api";

export function OfferDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [offer, setOffer] = useState<Offer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [applications, setApplications] = useState<ApplicationListItem[]>([]);

  useEffect(() => {
    if (!id) return;
    api.getOffer(id)
      .then((o) => {
        setOffer(o);
        setNotes(o.notes || "");
      })
      .catch((e) => setError(e.message));
    api
      .listApplications(new URLSearchParams({ offer_id: id, page_size: "20" }))
      .then((data) => setApplications(data.items))
      .catch(() => setApplications([]));
  }, [id]);

  const saveNotes = async () => {
    if (!offer) return;
    const updated = await api.updateOffer(offer.id, { notes });
    setOffer(updated);
  };

  const setStatus = async (status: OfferStatus) => {
    if (!offer) return;
    const updated = await api.updateOffer(offer.id, { status });
    setOffer(updated);
  };

  const deleteOffer = async () => {
    if (!offer) return;
    if (!confirm(`Supprimer « ${offer.title} » ?`)) return;
    await api.archiveOffer(offer.id);
    navigate("/offers");
  };

  if (error) return <p className="msg error">{error}</p>;
  if (!offer) return <p className="empty">Chargement…</p>;

  return (
    <div className="page offer-detail">
      <Link to="/offers" className="back">← Retour</Link>

      <div className="detail-header">
        <div>
          <h1>{offer.title}</h1>
          <p className="detail-meta">
            {offer.company}
            {offer.location && ` · ${offer.location}`}
          </p>
          <div className="detail-tags">
            <span className={`tag source-${offer.source}`}>{offer.source}</span>
            <span className={`tag status-${offer.status}`}>{offer.status}</span>
          </div>
        </div>
        <div>
          <a className="btn primary" href={offer.url} target="_blank" rel="noreferrer">
            Ouvrir l&apos;annonce
          </a>
          <Link
            className="btn ghost"
            to="/apply"
            state={{
              offerId: offer.id,
              offerText: [offer.title, offer.company, offer.description_raw]
                .filter(Boolean)
                .join("\n\n"),
            }}
          >
            CV / lettre
          </Link>
        </div>
      </div>

      <div className="detail-actions">
        <button className="btn ghost" onClick={() => setStatus("shortlisted")}>Shortlist</button>
        <button className="btn ghost" onClick={() => setStatus("reviewed")}>Revue</button>
        <button className="btn ghost danger-text" onClick={deleteOffer}>Supprimer</button>
      </div>

      <section className="card">
        <h2>Description</h2>
        <pre className="description">{offer.description_raw || "Pas de description"}</pre>
      </section>

      <section className="card">
        <h2>Candidatures</h2>
        {applications.length === 0 ? (
          <p className="hint">Pas encore de CV généré pour cette offre.</p>
        ) : (
          <ul className="offer-list">
            {applications.map((app) => (
              <li key={app.id}>
                <Link to={`/applications/${app.id}`}>
                  {app.job_title || "CV"} — {new Date(app.created_at).toLocaleDateString("fr-FR")}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card">
        <h2>Notes</h2>
        <textarea
          className="notes-input"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={4}
          placeholder="Tes notes sur cette offre…"
        />
        <button className="btn" onClick={saveNotes}>Enregistrer</button>
      </section>
    </div>
  );
}
