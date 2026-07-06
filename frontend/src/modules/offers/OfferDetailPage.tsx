import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, Offer, OfferStatus } from "../../shared/api";

export function OfferDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [offer, setOffer] = useState<Offer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState("");

  useEffect(() => {
    if (!id) return;
    api.getOffer(id)
      .then((o) => {
        setOffer(o);
        setNotes(o.notes || "");
      })
      .catch((e) => setError(e.message));
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

  if (error) return <p className="error">{error}</p>;
  if (!offer) return <p>Chargement...</p>;

  return (
    <div className="offer-detail">
      <Link to="/offers">← Retour</Link>
      <h2>{offer.title}</h2>
      <p className="meta">
        <strong>{offer.company}</strong>
        {offer.location && ` · ${offer.location}`}
        {" · "}
        <span className={`badge source-${offer.source}`}>{offer.source}</span>
        {" · "}
        <span className={`badge status-${offer.status}`}>{offer.status}</span>
      </p>

      <div className="actions-bar">
        <a className="btn primary" href={offer.url} target="_blank" rel="noreferrer">
          Ouvrir l&apos;annonce
        </a>
        <button onClick={() => setStatus("shortlisted")}>Shortlister</button>
        <button onClick={() => setStatus("reviewed")}>Marquer revue</button>
        <button onClick={() => setStatus("archived")}>Archiver</button>
      </div>

      {offer.contract_type && <p><strong>Contrat :</strong> {offer.contract_type}</p>}
      {offer.posted_at && (
        <p><strong>Publiée :</strong> {new Date(offer.posted_at).toLocaleDateString("fr-FR")}</p>
      )}

      <h3>Description</h3>
      <pre className="description">{offer.description_raw || "Pas de description"}</pre>

      <h3>Notes</h3>
      <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={4} />
      <button onClick={saveNotes}>Enregistrer les notes</button>
    </div>
  );
}
