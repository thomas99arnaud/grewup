import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  api,
  ApplicationDetail,
  ApplicationStatus,
  APPLICATION_STATUS_LABELS,
} from "../../shared/api";
import { downloadPdf, PdfFrame } from "./pdf";

const STATUSES: ApplicationStatus[] = ["draft", "applied", "interview", "rejected", "hired"];

export function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [row, setRow] = useState<ApplicationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!id) return;
    api
      .getApplication(id)
      .then((data) => {
        setRow(data);
        setNotes(data.notes || "");
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Erreur"));
  }, [id]);

  const setStatus = async (status: ApplicationStatus) => {
    if (!row) return;
    const updated = await api.updateApplication(row.application_id, { status });
    setRow((prev) => (prev ? { ...prev, status: updated.status, applied_at: updated.applied_at } : prev));
  };

  const saveNotes = async (e: FormEvent) => {
    e.preventDefault();
    if (!row) return;
    setSaving(true);
    try {
      const updated = await api.updateApplication(row.application_id, { notes });
      setRow((prev) => (prev ? { ...prev, notes: updated.notes } : prev));
    } finally {
      setSaving(false);
    }
  };

  if (error) return <p className="msg error">{error}</p>;
  if (!row) return <p className="empty">Chargement…</p>;

  return (
    <div className="page generate-page">
      <Link to="/applications" className="back">
        ← Candidatures
      </Link>
      <div className="page-head compact">
        <h1>
          {row.job_title}
          {row.company ? ` — ${row.company}` : ""}
        </h1>
        <span className={`tag status-${row.status}`}>{APPLICATION_STATUS_LABELS[row.status]}</span>
      </div>
      <p className="hint">{row.fit_summary}</p>
      {row.reused && (
        <p className="reuse-banner">
          CV réutilisé
          {row.reused_from_title ? ` depuis ${row.reused_from_title}` : ""}
          {row.reused_from_company ? ` — ${row.reused_from_company}` : ""}.
        </p>
      )}
      {row.emphasized_experiences.length > 0 && (
        <p className="hint">Gardé : {row.emphasized_experiences.join(" · ")}</p>
      )}
      {(row.omitted_experiences?.length ?? 0) > 0 && (
        <p className="hint">Omise : {row.omitted_experiences.join(" · ")}</p>
      )}

      <div className="detail-actions">
        {STATUSES.map((status) => (
          <button
            key={status}
            type="button"
            className={`btn ghost${row.status === status ? " active-status" : ""}`}
            onClick={() => setStatus(status)}
          >
            {APPLICATION_STATUS_LABELS[status]}
          </button>
        ))}
        {row.offer_id && (
          <Link className="btn ghost" to={`/offers/${row.offer_id}`}>
            Offre
          </Link>
        )}
      </div>

      <div className="pdf-actions">
        <button
          type="button"
          className="btn primary"
          onClick={() => downloadPdf(row.cv_pdf_base64, row.cv_filename)}
        >
          Télécharger le CV (PDF)
        </button>
        <button
          type="button"
          className="btn primary"
          onClick={() => downloadPdf(row.letter_pdf_base64, row.letter_filename)}
        >
          Télécharger la lettre (PDF)
        </button>
      </div>

      <div className="generate-results">
        <section className="card">
          <div className="card-head">
            <h2>CV</h2>
          </div>
          <PdfFrame base64={row.cv_pdf_base64} />
        </section>
        <section className="card">
          <div className="card-head">
            <h2>Lettre</h2>
          </div>
          <PdfFrame base64={row.letter_pdf_base64} />
        </section>
      </div>

      <section className="card">
        <h2>Notes</h2>
        <form onSubmit={saveNotes}>
          <textarea
            className="notes-input"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={4}
            placeholder="Relance, contact, date d’entretien…"
          />
          <button type="submit" className="btn" disabled={saving}>
            {saving ? "…" : "Enregistrer"}
          </button>
        </form>
      </section>
    </div>
  );
}
