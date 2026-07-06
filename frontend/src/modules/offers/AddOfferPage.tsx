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
    <div>
      <h2>Ajouter une offre</h2>
      <div className="tabs">
        <button className={tab === "url" ? "active" : ""} onClick={() => setTab("url")}>
          Par URL
        </button>
        <button className={tab === "manual" ? "active" : ""} onClick={() => setTab("manual")}>
          Collage manuel
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {tab === "url" ? (
        <form onSubmit={handleUrl} className="form">
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
          <p className="hint">
            Détection auto : WTTJ, Indeed, Greenhouse, Lever. Autres sites : extraction générique.
          </p>
          <button type="submit" disabled={loading}>
            {loading ? "Import..." : "Importer"}
          </button>
        </form>
      ) : (
        <form onSubmit={handleManual} className="form">
          <label>
            Titre *
            <input value={title} onChange={(e) => setTitle(e.target.value)} required />
          </label>
          <label>
            Entreprise *
            <input value={company} onChange={(e) => setCompany(e.target.value)} required />
          </label>
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
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={10}
            />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? "Création..." : "Créer"}
          </button>
        </form>
      )}
    </div>
  );
}
