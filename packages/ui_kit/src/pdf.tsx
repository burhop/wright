import { useEffect, useRef, useState } from "react";
import { ImageThumbnail } from "./inputs";

/** A passive page from the same authorized PDF; forms and links are not active. */
export function PdfPageViewer({ blob, title, sourceSha256, readPage, onReady }: {
  blob: Blob;
  title: string;
  sourceSha256?: string;
  readPage?: (page: number, signal: AbortSignal) => Promise<Blob>;
  onReady?: () => void;
}) {
  const [selection, setSelection] = useState({ blob, page: 1 });
  const page = selection.blob === blob ? selection.page : 1;
  const [enlargement, setEnlargement] = useState({ blob, enlarged: false });
  const enlarged = enlargement.blob === blob && enlargement.enlarged;
  const [view, setView] = useState<{ blob: Blob; page: number; sourceSha256?: string; count?: number; image?: Blob; error?: string }>();
  const reader = useRef(readPage);
  reader.current = readPage;
  const available = !!readPage;
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setView(undefined);
    const open = async () => {
      if (!sourceSha256 || !reader.current || blob.size > 20 * 1024 * 1024)
        throw Error("PDF preview unavailable");
      const response = await reader.current(page, controller.signal);
      if (response.type !== "application/vnd.wright.pdf-page+json" || response.size > 8 * 1024 * 1024)
        throw Error("Unsupported PDF view");
      const data = JSON.parse(await response.text());
      if (data.format !== "wright.pdf.page.v1" || data.source_sha256 !== sourceSha256 ||
          data.page !== page || !Number.isInteger(data.page_count) || data.page_count < page || data.page_count > 200 ||
          !Number.isInteger(data.width) || !Number.isInteger(data.height) || data.width < 1 || data.height < 1 ||
          data.width > 1800 || data.height > 1800 || typeof data.png_base64 !== "string")
        throw Error("PDF identity or page bound mismatch");
      const decoded = atob(data.png_base64);
      const bytes = Uint8Array.from(decoded, c => c.charCodeAt(0));
      if (bytes.length < 24 || bytes[0] !== 137 || String.fromCharCode(...bytes.slice(1, 4)) !== "PNG")
        throw Error("PDF page image unavailable");
      const header = new DataView(bytes.buffer);
      if (header.getUint32(16) !== data.width || header.getUint32(20) !== data.height)
        throw Error("PDF page dimensions mismatch");
      if (active) setView({ blob, page, sourceSha256, count: data.page_count, image: new Blob([bytes], { type: "image/png" }) });
    };
    void open().catch(() => {
      if (active) setView({ blob, page, sourceSha256, error: "This PDF page could not be previewed. Download the exact PDF to inspect it." });
    });
    return () => { active = false; controller.abort(); };
  }, [blob, page, sourceSha256, available]);
  const current = view?.blob === blob && view.page === page && view.sourceSha256 === sourceSha256 ? view : undefined;
  const ready = useRef(onReady);
  ready.current = onReady;
  useEffect(() => { if (current?.error) ready.current?.(); }, [current]);
  return <section className="wp-pdf-preview" aria-label="PDF drawing preview">
    {current?.image && <>
      <div className="wp-row">
        <button type="button" disabled={page <= 1} onClick={() => setSelection({ blob, page: page - 1 })}>Previous page</button>
        <span>Page {page} of {current.count}</span>
        <button type="button" disabled={page >= (current.count ?? 1)} onClick={() => setSelection({ blob, page: page + 1 })}>Next page</button>
        <button type="button" aria-pressed={enlarged} onClick={() => setEnlargement({ blob, enlarged: !enlarged })}>{enlarged ? "Fit drawing" : "Enlarge drawing"}</button>
      </div>
      <div className={`wp-pdf-sheet${enlarged ? " is-full-size" : ""}`} role="region" aria-label="PDF page" tabIndex={0}>
        <ImageThumbnail blob={current.image} title={`${title} · page ${page}`} onReady={onReady} />
      </div>
    </>}
    {!current && <p role="status">Opening PDF page…</p>}
    {current?.error && <p role="status">{current.error}</p>}
  </section>;
}
