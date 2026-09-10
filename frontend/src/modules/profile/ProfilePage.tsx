import { useState } from "react";
import { DossierEditor } from "./DossierEditor";

export function ProfilePage() {
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="page word-page">
      {error && <p className="msg error word-error">{error}</p>}
      <DossierEditor onError={setError} />
    </div>
  );
}
