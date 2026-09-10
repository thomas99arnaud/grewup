import { FormEvent, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { api, GeneratedApplication } from "../../shared/api";

function downloadPdf(base64: string, filename: string) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  const url = URL.createObjectURL(new Blob([bytes], { type: "application/pdf" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function PdfFrame({ base64 }: { base64: string }) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    const objectUrl = URL.createObjectURL(new Blob([bytes], { type: "application/pdf" }));
    setUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [base64]);
  if (!url) return null;
  return <iframe className="pdf-frame" title="Aperçu PDF" src={url} />;
}

export function GeneratePage() {
  const location = useLocation();
  const fromOffer =
    location.state && typeof location.state === "object" && "offerText" in location.state
      ? String((location.state as { offerText?: string }).offerText || "")
      : "";
  const [offerText, setOfferText] = useState(fromOffer);
  const [language, setLanguage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GeneratedApplication | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await api.generateApplication({
        offer_text: offerText,
        language: language || null,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page generate-page">
      <h1>CV et lettre</h1>
      <p className="subtitle">
        Colle une offre. L&apos;IA s&apos;appuie sur le suivi de compétences du Répertoire
        (le même fichier Word), choisit les expériences utiles, puis exporte deux PDF.
      </p>

      <div className="card">
        {error && <p className="msg error">{error}</p>}
        <form onSubmit={handleSubmit} className="scrape-form">
          <label>
            Texte de l&apos;offre
            <textarea
              value={offerText}
              onChange={(e) => setOfferText(e.target.value)}
              rows={14}
              placeholder="Colle ici l’annonce (intitulé, entreprise, missions, stack…)"
              required
            />
          </label>
          <label>
            Langue
            <select value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="">Détecter (recommandé)</option>
              <option value="fr">Français</option>
              <option value="en">English</option>
            </select>
          </label>
          <button type="submit" className="btn primary" disabled={loading || offerText.trim().length < 40}>
            {loading ? "Rédaction…" : "Générer CV et lettre"}
          </button>
        </form>
      </div>

      {result && (
        <>
          <section className="card">
            <h2>
              {result.job_title}
              {result.company ? ` — ${result.company}` : ""}
            </h2>
            <p className="hint">{result.fit_summary}</p>
            {result.emphasized_experiences.length > 0 && (
              <p className="hint">
                Gardé : {result.emphasized_experiences.join(" · ")}
              </p>
            )}
            {(result.omitted_experiences?.length ?? 0) > 0 && (
              <p className="hint">
                Omise : {result.omitted_experiences.join(" · ")}
              </p>
            )}
            <div className="pdf-actions">
              <button
                type="button"
                className="btn primary"
                onClick={() => downloadPdf(result.cv_pdf_base64, result.cv_filename)}
              >
                Télécharger le CV (PDF)
              </button>
              <button
                type="button"
                className="btn primary"
                onClick={() => downloadPdf(result.letter_pdf_base64, result.letter_filename)}
              >
                Télécharger la lettre (PDF)
              </button>
            </div>
          </section>

          <div className="generate-results">
            <section className="card">
              <div className="card-head">
                <h2>CV</h2>
                <button
                  type="button"
                  className="btn ghost"
                  onClick={() => downloadPdf(result.cv_pdf_base64, result.cv_filename)}
                >
                  PDF
                </button>
              </div>
              <PdfFrame base64={result.cv_pdf_base64} />
            </section>
            <section className="card">
              <div className="card-head">
                <h2>Lettre</h2>
                <button
                  type="button"
                  className="btn ghost"
                  onClick={() => downloadPdf(result.letter_pdf_base64, result.letter_filename)}
                >
                  PDF
                </button>
              </div>
              <PdfFrame base64={result.letter_pdf_base64} />
            </section>
          </div>
        </>
      )}
    </div>
  );
}
