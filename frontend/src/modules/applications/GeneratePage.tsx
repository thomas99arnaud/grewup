import { FormEvent, useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api, GeneratedApplication } from "../../shared/api";
import { downloadPdf, PdfFrame } from "./pdf";

type ApplyState = {
  offerText?: string;
  offerId?: string;
};

export function GeneratePage() {
  const location = useLocation();
  const fromState =
    location.state && typeof location.state === "object" ? (location.state as ApplyState) : {};
  const [offerText, setOfferText] = useState(fromState.offerText || "");
  const [offerId, setOfferId] = useState(fromState.offerId || "");
  const [language, setLanguage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GeneratedApplication | null>(null);

  useEffect(() => {
    if (fromState.offerText) setOfferText(fromState.offerText);
    if (fromState.offerId) setOfferId(fromState.offerId);
  }, [fromState.offerText, fromState.offerId]);

  const generate = async (force: boolean) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.generateApplication({
        offer_text: offerText,
        offer_id: offerId || null,
        language: language || null,
        force,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await generate(false);
  };

  return (
    <div className="page generate-page">
      <h1>CV et lettre</h1>
      <p className="subtitle">
        Colle une offre. L&apos;IA sélectionne les expériences, réutilise un CV déjà produit
        s&apos;il collerait au même profil, et écrit toujours une nouvelle lettre.
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
            {result.reused && (
              <p className="reuse-banner">
                CV réutilisé
                {result.reused_from_title ? ` depuis ${result.reused_from_title}` : ""}
                {result.reused_from_company ? ` — ${result.reused_from_company}` : ""}.
                Nouvelle lettre uniquement.
              </p>
            )}
            <p className="hint">{result.fit_summary}</p>
            {result.emphasized_experiences.length > 0 && (
              <p className="hint">Gardé : {result.emphasized_experiences.join(" · ")}</p>
            )}
            {(result.omitted_experiences?.length ?? 0) > 0 && (
              <p className="hint">Omise : {result.omitted_experiences.join(" · ")}</p>
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
              {result.application_id && (
                <Link className="btn ghost" to={`/applications/${result.application_id}`}>
                  Voir la candidature
                </Link>
              )}
              {result.reused && (
                <button
                  type="button"
                  className="btn ghost"
                  disabled={loading}
                  onClick={() => generate(true)}
                >
                  Régénérer le CV
                </button>
              )}
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
