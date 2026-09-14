import { useState } from "react";
import { api, ApplicationDetail, GeneratedApplication } from "../../shared/api";
import { downloadPdf, PdfFrame } from "./pdf";

type Docs = Pick<
  GeneratedApplication,
  | "application_id"
  | "cv_markdown"
  | "cover_letter"
  | "cv_pdf_base64"
  | "letter_pdf_base64"
  | "cv_filename"
  | "letter_filename"
>;

export function DocumentEditors({
  docs,
  onDocsChange,
}: {
  docs: Docs;
  onDocsChange: (next: Docs) => void;
}) {
  const [cvText, setCvText] = useState(docs.cv_markdown);
  const [letterText, setLetterText] = useState(docs.cover_letter);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dirty = cvText !== docs.cv_markdown || letterText !== docs.cover_letter;

  const applyDetail = (detail: ApplicationDetail) => {
    setCvText(detail.cv_markdown);
    setLetterText(detail.cover_letter);
    onDocsChange({
      application_id: detail.application_id,
      cv_markdown: detail.cv_markdown,
      cover_letter: detail.cover_letter,
      cv_pdf_base64: detail.cv_pdf_base64,
      letter_pdf_base64: detail.letter_pdf_base64,
      cv_filename: detail.cv_filename,
      letter_filename: detail.letter_filename,
    });
  };

  const saveAndPreview = async () => {
    setSaving(true);
    setError(null);
    try {
      const detail = await api.updateApplication(docs.application_id, {
        cv_markdown: cvText,
        cover_letter: letterText,
      });
      applyDetail(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSaving(false);
    }
  };

  const exportPdf = async (kind: "cv" | "letter") => {
    let next = docs;
    if (dirty) {
      setSaving(true);
      setError(null);
      try {
        const detail = await api.updateApplication(docs.application_id, {
          cv_markdown: cvText,
          cover_letter: letterText,
        });
        applyDetail(detail);
        next = {
          application_id: detail.application_id,
          cv_markdown: detail.cv_markdown,
          cover_letter: detail.cover_letter,
          cv_pdf_base64: detail.cv_pdf_base64,
          letter_pdf_base64: detail.letter_pdf_base64,
          cv_filename: detail.cv_filename,
          letter_filename: detail.letter_filename,
        };
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erreur");
        setSaving(false);
        return;
      }
      setSaving(false);
    }
    if (kind === "cv") downloadPdf(next.cv_pdf_base64, next.cv_filename);
    else downloadPdf(next.letter_pdf_base64, next.letter_filename);
  };

  return (
    <>
      {error && <p className="msg error">{error}</p>}
      <div className="pdf-actions">
        <button type="button" className="btn" disabled={!dirty || saving} onClick={saveAndPreview}>
          {saving ? "Mise à jour…" : "Mettre à jour l’aperçu"}
        </button>
        <button type="button" className="btn primary" disabled={saving} onClick={() => exportPdf("cv")}>
          Exporter le CV
        </button>
        <button type="button" className="btn primary" disabled={saving} onClick={() => exportPdf("letter")}>
          Exporter la lettre
        </button>
      </div>
      <div className="generate-results">
        <section className="card">
          <div className="card-head">
            <h2>CV</h2>
          </div>
          <textarea
            className="doc-editor"
            value={cvText}
            onChange={(e) => setCvText(e.target.value)}
            rows={18}
            spellCheck
          />
          <PdfFrame base64={docs.cv_pdf_base64} />
        </section>
        <section className="card">
          <div className="card-head">
            <h2>Lettre</h2>
          </div>
          <textarea
            className="doc-editor"
            value={letterText}
            onChange={(e) => setLetterText(e.target.value)}
            rows={18}
            spellCheck
          />
          <PdfFrame base64={docs.letter_pdf_base64} />
        </section>
      </div>
    </>
  );
}
