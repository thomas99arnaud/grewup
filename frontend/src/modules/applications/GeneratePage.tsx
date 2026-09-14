import { FormEvent, useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api, GeneratedApplication } from "../../shared/api";
import { DocumentEditors } from "./DocumentEditors";

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
        Colle une offre. Tu peux ensuite corriger le CV et la lettre, mettre à jour
        l&apos;aperçu, puis exporter les PDF.
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

          <DocumentEditors
            key={result.application_id}
            docs={result}
            onDocsChange={(next) => setResult((prev) => (prev ? { ...prev, ...next } : prev))}
          />
        </>
      )}
    </div>
  );
}
