import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../shared/api";

type Tab = "url" | "manual";

export function AddOfferPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>("url");
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUrl = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const offer = await api.importUrl(url);
      navigate(`/offers/${offer.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  };

  const handleManual = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const offer = await api.createManual({
        title,
        company,
        location: location || null,
        description_raw: description,
        url: url || undefined,
      });
      navigate(`/offers/${offer.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <h1>Ajouter une offre</h1>

      <div className="tabs">
        <button className={tab === "url" ? "active" : ""} onClick={() => setTab("url")}>
          Par URL
        </button>
        <button className={tab === "manual" ? "active" : ""} onClick={() => setTab("manual")}>
          Saisie manuelle
        </button>
      </div>

      <div className="card">
        {error && <p className="msg error">{error}</p>}

        {tab === "url" ? (
          <form onSubmit={handleUrl} className="scrape-form">
            <label>
              URL de l&apos;annonce
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://..."
                required
              />
            </label>
            <p className="hint">WTTJ, Indeed, Greenhouse, Lever — ou extraction générique.</p>
            <button type="submit" className="btn primary" disabled={loading}>
              {loading ? "Import…" : "Importer"}
            </button>
          </form>
        ) : (
          <form onSubmit={handleManual} className="scrape-form">
            <div className="form-row">
              <label>
                Titre *
                <input value={title} onChange={(e) => setTitle(e.target.value)} required />
              </label>
              <label>
                Entreprise *
                <input value={company} onChange={(e) => setCompany(e.target.value)} required />
              </label>
            </div>
            <label>
              Lieu
              <input value={location} onChange={(e) => setLocation(e.target.value)} />
            </label>
            <label>
              URL (optionnel)
              <input type="url" value={url} onChange={(e) => setUrl(e.target.value)} />
            </label>
            <label>
              Description
              <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={8} />
            </label>
            <button type="submit" className="btn primary" disabled={loading}>
              {loading ? "Création…" : "Créer"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
