import { useEffect, useState } from "react";

export function downloadPdf(base64: string, filename: string) {
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

export function PdfFrame({ base64 }: { base64: string }) {
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
