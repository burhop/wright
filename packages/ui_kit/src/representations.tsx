import { useEffect, useId, useRef, useState } from "react";
import type { JsonValue } from "@wright/process-client";
import { ImageThumbnail } from "./inputs";
import { useFileDownload, fileDownloadMessage, type FileDownloadRequest } from "./file-download";
import { ThreeDViewer, ToolpathViewer } from "./geometry";
import { MarkdownDocument } from "./documents";
import { PdfPageViewer } from "./pdf";
import { AssessmentReportViewer, isAssessmentRecord } from "./assessment";
import {
  parseRecordedToolpaths,
  parseToolpaths,
  type ToolpathDocument,
} from "./toolpaths";

/** A bounded, passive view of supplied fields; no inferred units or verdicts. */
function RecordedValue({ value, depth = 0 }: { value: JsonValue; depth?: number }) {
  const [expanded, setExpanded] = useState(depth === 0);
  const [limit, setLimit] = useState(25);
  if (value === null) return <span className="wp-muted">No value</span>;
  if (typeof value === "boolean") return <span>{value ? "Yes" : "No"}</span>;
  if (typeof value !== "object") return <span>{String(value)}</span>;
  const isArray = Array.isArray(value);
  const entries = isArray
    ? value.map((item, index) => [String(index + 1), item] as const)
    : Object.entries(value);
  if (!entries.length) return <span className="wp-muted">{isArray ? "No items" : "No fields"}</span>;
  if (depth >= 6) return <span className="wp-muted">Further detail is available in the file download.</span>;
  const table = (
    <div className="wp-table">
      <table>
        <thead><tr><th scope="col">{isArray ? "Item" : "Field"}</th><th scope="col">Value</th></tr></thead>
        <tbody>{entries.slice(0, limit).map(([key, item]) => (
          <tr key={key}>
            <th scope="row" title={key}>{isArray ? key : key.replaceAll("_", " ")}</th>
            <td><RecordedValue value={item} depth={depth + 1} /></td>
          </tr>
        ))}</tbody>
      </table>
      {entries.length > limit && <button type="button" className="wp-link" onClick={() => setLimit((current) => current + 25)}>
        Show more ({entries.length - limit} remaining)
      </button>}
    </div>
  );
  if (depth === 0) return table;
  return <details onToggle={(event) => setExpanded(event.currentTarget.open)}>
    <summary>{entries.length} {isArray ? "items" : "fields"}</summary>
    {expanded && table}
  </details>;
}

/** Download the exact bytes supplied by the scoped representation owner. */
export function RepresentationDownload({ blob, name }: { blob: Blob; name: string }) {
  const request = useFileDownload();
  return request
    ? <HostRepresentationDownload key={name} blob={blob} name={name} request={request} />
    : <BrowserRepresentationDownload blob={blob} name={name} />;
}
function HostRepresentationDownload({ blob, name, request }: { blob: Blob; name: string; request: FileDownloadRequest }) {
  const pending = useRef(false);
  const generation = useRef(0);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  useEffect(() => {
    const current = ++generation.current;
    pending.current = false;
    setBusy(false);
    setMessage("");
    return () => { generation.current = current + 1; };
  }, [blob, name]);
  async function download() {
    if (pending.current) return;
    pending.current = true;
    const current = generation.current;
    setBusy(true);
    setMessage("");
    try {
      const result = await request(blob, name.replaceAll("\\", "/").split("/").at(-1) || "representation");
      if (current === generation.current) setMessage(fileDownloadMessage(result));
    } catch {
      if (current === generation.current) setMessage("The download was not confirmed. Check your downloads before trying again.");
    } finally {
      if (current === generation.current) {
        pending.current = false;
        setBusy(false);
      }
    }
  }
  return <div>
    <button type="button" className="wp-link" disabled={busy} onClick={() => void download()}>
      {busy ? "Preparing download…" : "Download exact file"}
    </button>
    {message && <p role="status">{message}</p>}
  </div>;
}
function BrowserRepresentationDownload({ blob, name }: { blob: Blob; name: string }) {
  const [link, setLink] = useState<{ blob: Blob; url: string }>();
  const [error, setError] = useState(false);
  useEffect(() => {
    setError(false);
    setLink(undefined);
    try {
      const url = URL.createObjectURL(blob);
      setLink({ blob, url });
      return () => URL.revokeObjectURL(url);
    } catch {
      setError(true);
    }
  }, [blob]);
  if (error) return <p role="status">File download is unavailable in this view.</p>;
  return link?.blob === blob ? (
    <a className="wp-link" href={link.url} download={name.replaceAll("\\", "/").split("/").at(-1) || "representation"}>
      Download exact file
    </a>
  ) : null;
}

export function DataTable({
  columns,
  rows,
  pageSize = 100,
}: {
  columns: readonly string[];
  rows: readonly (readonly JsonValue[])[];
  pageSize?: number;
}) {
  const [page, setPage] = useState(0);
  const size = Math.min(200, Math.max(1, pageSize));
  const count = Math.ceil(rows.length / size);
  const current = Math.min(page, Math.max(0, count - 1));
  if (
    columns.length > 50 ||
    rows.length > 10000 ||
    rows.some((row) => row.length !== columns.length)
  )
    return (
      <p role="status">
        This table exceeds its supported view bounds. Download the exact data to
        inspect it.
      </p>
    );
  return (
    <div className="wp-table">
      <table>
        <thead>
          <tr>
            {columns.map((column, index) => (
              <th scope="col" key={index}>
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows
            .slice(current * size, (current + 1) * size)
            .map((row, index) => (
              <tr key={index}>
                {row.map((cell, column) => (
                  <td key={column}>
                    <RecordedValue value={cell} depth={1} />
                  </td>
                ))}
              </tr>
            ))}
        </tbody>
      </table>
      {count > 1 && (
        <div className="wp-row">
          <button
            type="button"
            className="wp-link"
            disabled={current === 0}
            onClick={() => setPage(current - 1)}
          >
            Previous rows
          </button>
          <span>
            Page {current + 1} of {count}
          </span>
          <button
            type="button"
            className="wp-link"
            disabled={current + 1 >= count}
            onClick={() => setPage(current + 1)}
          >
            Next rows
          </button>
        </div>
      )}
    </div>
  );
}

/** Deliberately bounded CSV reader, including quoted commas/newlines/escaped quotes. */
export function parseCsv(text: string): {
  columns: string[];
  rows: string[][];
} {
  if (new TextEncoder().encode(text).length > 2 * 1024 * 1024)
    throw new Error("CSV view exceeds 2 MiB.");
  if (text.startsWith("\ufeff")) text = text.slice(1);
  const records: string[][] = [];
  let row: string[] = [],
    field = "",
    quoted = false,
    closed = false;
  const addField = () => {
    if (field.length > 8192 || row.length >= 50)
      throw new Error("CSV field view exceeds its bounds.");
    row.push(field);
    field = "";
    closed = false;
  };
  const addRow = () => {
    addField();
    if (row.length !== 1 || row[0] !== "") records.push(row);
    row = [];
    if (records.length > 10001)
      throw new Error("CSV row view exceeds its bounds.");
  };
  for (let index = 0; index < text.length; index++) {
    const character = text[index];
    if (quoted) {
      if (character === '"' && text[index + 1] === '"') {
        field += '"';
        index++;
      } else if (character === '"') {
        quoted = false;
        closed = true;
      } else field += character;
    } else if (character === '"' && field === "" && !closed) quoted = true;
    else if (character === ",") addField();
    else if (character === "\n" || character === "\r") {
      if (character === "\r" && text[index + 1] === "\n") index++;
      addRow();
    } else {
      if (closed || character === '"')
        throw new Error("CSV quote structure is unsupported.");
      field += character;
    }
  }
  if (quoted) throw new Error("CSV contains an unterminated quote.");
  if (field !== "" || row.length || closed) addRow();
  const columns = records.shift();
  if (!columns || records.some((record) => record.length !== columns.length))
    throw new Error("CSV needs consistent columns.");
  return { columns, rows: records };
}
// Display rounding never changes the plotted coordinates or retained data.
function plotTicks(min: number, max: number) {
  const values = min === max ? [min] : [...new Set(
    Array.from({ length: 5 }, (_, index) =>
      index === 4 ? max : min + (max - min) * (index / 4)),
  )];
  const rounded = values.map(value => String(Number(value.toPrecision(6))));
  const distinct = new Set(rounded).size === values.length;
  return values.map((value, index) => ({ value, label: distinct ? rounded[index] : String(value) }));
}

function plotPosition(value: number, min: number, max: number, start: number, end: number) {
  return min === max ? (start + end) / 2 : start + ((value - min) / (max - min)) * (end - start);
}

function PlotAxes({ minX, maxX, minY, maxY, xLabel, yLabel }: {
  minX: number; maxX: number; minY: number; maxY: number;
  xLabel: string; yLabel: string;
}) {
  return <g fill="currentColor" fontSize="12">
    <path d="M80 30V250H550" fill="none" stroke="currentColor" />
    <g aria-label={`${xLabel} axis`}>
      {plotTicks(minX, maxX).map(({ value, label }) => {
        const x = plotPosition(value, minX, maxX, 80, 550);
        return <g key={value}>
          <title>{String(value)}</title>
          <path d={`M${x} 250v6`} stroke="currentColor" />
          <text x={x} y="273" textAnchor="middle">{label}</text>
        </g>;
      })}
    </g>
    <g aria-label={`${yLabel} axis`}>
      {plotTicks(minY, maxY).map(({ value, label }) => {
        const y = plotPosition(value, minY, maxY, 250, 30);
        return <g key={value}>
          <title>{String(value)}</title>
          <path d={`M74 ${y}h6`} stroke="currentColor" />
          <text x="69" y={y + 4} textAnchor="end">{label}</text>
        </g>;
      })}
    </g>
    <text x="315" y="303" textAnchor="middle" fontSize="14">{xLabel}</text>
    <text x="15" y="140" transform="rotate(-90 15 140)" textAnchor="middle" fontSize="14">{yLabel}</text>
  </g>;
}

export function NumericPlot({
  points,
  xLabel,
  yLabel,
  title,
}: {
  points: readonly (readonly [number, number])[];
  xLabel: string;
  yLabel: string;
  title: string;
}) {
  if (
    !points.length ||
    points.length > 10000 ||
    points.some(
      (point) =>
        point.length !== 2 || point.some((value) => !Number.isFinite(value)),
    )
  )
    return <p role="status">A finite bounded plot is unavailable.</p>;
  let minX = Infinity,
    maxX = -Infinity,
    minY = Infinity,
    maxY = -Infinity;
  for (const [x, y] of points) {
    minX = Math.min(minX, x);
    maxX = Math.max(maxX, x);
    minY = Math.min(minY, y);
    maxY = Math.max(maxY, y);
  }
  if (!Number.isFinite(maxX - minX) || !Number.isFinite(maxY - minY))
    return (
      <p role="status">The plot extent exceeds its supported numeric range.</p>
    );
  const coordinates = points
    .map(
      ([x, y]) =>
        `${plotPosition(x, minX, maxX, 80, 550)},${plotPosition(y, minY, maxY, 250, 30)}`,
    )
    .join(" ");
  return (
    <figure className="wp-plot">
      <figcaption>{title}</figcaption>
      <svg
        viewBox="0 0 620 325"
        role="img"
        aria-label={`${title}; ${xLabel} from ${minX} to ${maxX}; ${yLabel} from ${minY} to ${maxY}`}
      >
        <PlotAxes {...{ minX, maxX, minY, maxY, xLabel, yLabel }} />
        <polyline
          points={coordinates}
          fill="none"
          stroke="var(--color-secondary)"
          strokeWidth="2"
        />
      </svg>
      <p className="wp-muted">
        Plotted supplied data; acceptance remains with the linked assessments.
      </p>
    </figure>
  );
}

export function ScalarFieldPlot({
  points,
  xLabel,
  yLabel,
  valueLabel,
  title,
}: {
  points: readonly { x: number; y: number; value: number }[];
  xLabel: string;
  yLabel: string;
  valueLabel: string;
  title: string;
}) {
  const gradientId = `wp-field-${useId()}`;
  if (
    !points.length ||
    points.length > 10000 ||
    points.some(
      (point) => ![point.x, point.y, point.value].every(Number.isFinite),
    )
  )
    return <p role="status">A finite bounded field view is unavailable.</p>;
  let minX = Infinity,
    maxX = -Infinity,
    minY = Infinity,
    maxY = -Infinity,
    minV = Infinity,
    maxV = -Infinity;
  for (const point of points) {
    minX = Math.min(minX, point.x);
    maxX = Math.max(maxX, point.x);
    minY = Math.min(minY, point.y);
    maxY = Math.max(maxY, point.y);
    minV = Math.min(minV, point.value);
    maxV = Math.max(maxV, point.value);
  }
  if (![maxX - minX, maxY - minY, maxV - minV].every(Number.isFinite))
    return (
      <p role="status">The field extent exceeds its supported numeric range.</p>
    );
  return (
    <figure className="wp-plot">
      <figcaption>{title}</figcaption>
      <svg
        viewBox="0 0 760 325"
        role="img"
        aria-label={`${title}; ${valueLabel} samples from ${minV} to ${maxV}; ${xLabel}; ${yLabel}`}
      >
        <PlotAxes {...{ minX, maxX, minY, maxY, xLabel, yLabel }} />
        {points.map((point, index) => (
          <circle
            key={index}
            cx={plotPosition(point.x, minX, maxX, 80, 550)}
            cy={plotPosition(point.y, minY, maxY, 250, 30)}
            r={3}
            fill={`hsl(${240 * (1 - (point.value - minV) / (maxV - minV || 1))} 75% 50%)`}
          >
            <title>{`${xLabel}: ${point.x}; ${yLabel}: ${point.y}; ${valueLabel}: ${point.value}`}</title>
          </circle>
        ))}
        {minV !== maxV && <defs>
          <linearGradient id={gradientId} x1="0" y1="1" x2="0" y2="0">
            {[0, 0.25, 0.5, 0.75, 1].map(fraction => <stop
              key={fraction} offset={`${fraction * 100}%`}
              stopColor={`hsl(${240 * (1 - fraction)} 75% 50%)`}
            />)}
          </linearGradient>
        </defs>}
        <text x="605" y="16" fill="currentColor" fontSize="12">{valueLabel}</text>
        <g aria-label={`${valueLabel} color scale`} fill="currentColor" fontSize="12">
          <rect x="605" y="30" width="16" height="220"
            fill={minV === maxV ? "hsl(240 75% 50%)" : `url(#${gradientId})`} />
          {plotTicks(minV, maxV).map(({ value, label }) => {
            const y = plotPosition(value, minV, maxV, 250, 30);
            return <g key={value}>
              <path d={`M621 ${y}h5`} stroke="currentColor" />
              <text x="632" y={y + 4}>{label}</text>
            </g>;
          })}
        </g>
      </svg>
      <p>
        {valueLabel}: {minV}–{maxV}
      </p>
      <p className="wp-muted">
        Supplied samples without interpolated geometry. Review the exact
        assessment for acceptance.
      </p>
      <p className="wp-muted">Colors show the recorded value range, not pass or fail. Exact values remain in the table and sample tooltips.</p>
    </figure>
  );
}
/** Add whitespace without reserializing numbers, duplicate keys or string escapes. */
function readableJson(text: string): string {
  const tokens = text.match(/"(?:\\.|[^"\\])*"|[{}\[\],:]|[^\s{}\[\],:]+/g) ?? [];
  const parts: string[] = [];
  let depth = 0;
  let size = 0;
  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    let part = token;
    if (token === "{" || token === "[") {
      depth += 1;
      if (tokens[index + 1] !== (token === "{" ? "}" : "]"))
        part += "\n" + "  ".repeat(depth);
    } else if (token === "}" || token === "]") {
      depth -= 1;
      if (tokens[index - 1] !== (token === "}" ? "{" : "["))
        part = "\n" + "  ".repeat(depth) + token;
    } else if (token === ",") {
      part += "\n" + "  ".repeat(depth);
    } else if (token === ":") {
      part += " ";
    }
    size += part.length;
    if (size > 1024 * 1024) return text;
    parts.push(part);
  }
  const formatted = parts.join("");
  return new TextEncoder().encode(formatted).length <= 1024 * 1024
    ? formatted
    : text;
}

export function RepresentationViewer({
  blob,
  title,
  sourceSha256,
  readToolpaths,
  readPdfPage,
  readValidationReport,
  onReady,
}: {
  blob: Blob;
  title: string;
  sourceSha256?: string;
  /** Scoped read only; returns passive data from the exact same recorded artifact. */
  readToolpaths?: (signal: AbortSignal) => Promise<Blob>;
  readPdfPage?: (page: number, signal: AbortSignal) => Promise<Blob>;
  readValidationReport?: (signal: AbortSignal) => Promise<Blob>;
  /** The bounded preview or its fallback has committed; never an execution signal. */
  onReady?: () => void;
}) {
  const [data, setData] = useState<{
    blob: Blob;
    text?: string;
    bytes?: ArrayBuffer;
    toolpaths?: ToolpathDocument;
    assessment?: string;
    record?: JsonValue;
    message?: string;
  }>();
  const [error, setError] = useState<{ blob: Blob; message: string }>();
  const type = blob.type.split(";")[0];
  const readyCallback = useRef(onReady);
  readyCallback.current = onReady;
  const notifiedBlob = useRef<Blob | undefined>(undefined);
  useEffect(() => {
    if (((data?.blob === blob && data.assessment === undefined) || error?.blob === blob) && notifiedBlob.current !== blob) {
      notifiedBlob.current = blob;
      readyCallback.current?.();
    }
  }, [blob, data, error]);
  useEffect(() => {
    let active = true;
    setData(undefined);
    setError(undefined);
    if (
      [
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp",
        "model/3mf",
        "text/x-gcode",
        "application/vnd.wright.toolpaths+json",
        "application/pdf",
      ].includes(type)
    )
      return;
    const maximum = [
      "model/stl",
      "application/sla",
      "application/vnd.ms-pki.stl",
    ].includes(type)
      ? 32 * 1024 * 1024
      : type === "text/csv"
        ? 2 * 1024 * 1024
        : type === "application/json"
          ? 16 * 1024 * 1024
          : 65536;
    if (blob.size > maximum) {
      setError({
        blob,
        message:
          "This representation exceeds the supported preview size. Download it to inspect the complete file.",
      });
      return;
    }
    void (
      type.startsWith("text/") || type === "application/json"
        ? blob.text().then((text) => {
            if (type === "application/json") {
              let record: unknown;
              try {
                record = JSON.parse(text);
              } catch {
                return { text };
              }
              if (isAssessmentRecord(record)) return { assessment: text };
              // Historical or incomplete assessment data remains inspectable;
              // this raw view supplies no assessment or approval authority.
              if (record && typeof record === "object" && !Array.isArray(record) &&
                  (record as Record<string, unknown>).schema_version === "wright.process-validation/1")
                return { text: readableJson(text) };
              if (
                record &&
                typeof record === "object" &&
                !Array.isArray(record) &&
                (record as Record<string, unknown>).format ===
                  "wright.gcode.toolpaths.v1"
              ) {
                if (!sourceSha256)
                  throw new Error("Exact evidence identity is missing.");
                return {
                  toolpaths: parseRecordedToolpaths(record, sourceSha256),
                };
              }
              if (blob.size > 65536)
                return {
                  message:
                    "This representation exceeds the supported text preview size. Download it to inspect the complete file.",
                };
              // Undefined means parsing failed; malformed evidence stays verbatim.
              if (record !== undefined) return { text: readableJson(text) };
            }
            return { text };
          })
        : blob.arrayBuffer().then((bytes) => ({ bytes }))
    )
      .then((value) => {
        if (active) setData({ ...value, blob });
      })
      .catch(() => {
        if (active)
          setError({
            blob,
            message:
              "This representation could not be read. Download the exact file to inspect it.",
          });
      });
    return () => {
      active = false;
    };
  }, [blob, type, sourceSha256]);
  if (type === "application/pdf")
    return <PdfPageViewer blob={blob} title={title} sourceSha256={sourceSha256} readPage={readPdfPage} onReady={onReady} />;
  if (["image/png", "image/jpeg", "image/gif", "image/webp"].includes(type))
    return (
      <div className="wp-image-preview">
        <ImageThumbnail blob={blob} title={title} onReady={onReady} />
      </div>
    );
  if (
    [
      "model/3mf",
      "text/x-gcode",
      "application/vnd.wright.toolpaths+json",
    ].includes(type)
  )
    return (
      <RecordedToolpathPreview
        blob={blob}
        sourceSha256={sourceSha256}
        readToolpaths={readToolpaths}
        onReady={onReady}
      />
    );
  if (error?.blob === blob) return <p role="status">{error.message}</p>;
  if (!data || data.blob !== blob)
    return <p role="status">Opening representation…</p>;
  if (data.toolpaths) return <ToolpathViewer document={data.toolpaths} />;
  if (data.assessment !== undefined)
    return <AssessmentReportViewer blob={blob} source={data.assessment} readReport={readValidationReport} onReady={onReady} />;
  if (data.message) return <p role="status">{data.message}</p>;
  if (data.record !== undefined) return <RecordedValue key={sourceSha256 ?? title} value={data.record} />;
  if (
    data.bytes &&
    ["model/stl", "application/sla", "application/vnd.ms-pki.stl"].includes(
      type,
    )
  )
    return <ThreeDViewer arrayBuffer={data.bytes} fileName={title} />;
  if (data.text !== undefined && type === "text/csv") {
    try {
      const table = parseCsv(data.text);
      return <CsvNumericInspector {...table} />;
    } catch {
      return (
        <p role="status">
          A bounded table preview is unavailable. Download the complete CSV.
        </p>
      );
    }
  }
  if (data.text !== undefined && ["text/markdown", "text/x-markdown"].includes(type))
    return <MarkdownDocument text={data.text} />;
  if (
    data.text !== undefined &&
    type !== "text/html" &&
    type !== "image/svg+xml"
  )
    return <pre className="wp-text">{data.text}</pre>;
  return (
    <p role="status">
      This format has no supported preview. Open or download it with a suitable
      engineering tool.
    </p>
  );
}

/** Keeps the raw artifact/download separate from its passive derived view. */
export function RecordedToolpathPreview({
  blob,
  sourceSha256,
  readToolpaths,
  onReady,
}: {
  blob: Blob;
  sourceSha256?: string;
  readToolpaths?: (signal: AbortSignal) => Promise<Blob>;
  onReady?: () => void;
}) {
  const port = useRef(readToolpaths);
  port.current = readToolpaths;
  const available = Boolean(readToolpaths);
  const [state, setState] = useState<{
    blob: Blob;
    document?: ToolpathDocument;
    error?: string;
  }>();
  const readyCallback = useRef(onReady);
  readyCallback.current = onReady;
  const notifiedBlob = useRef<Blob | undefined>(undefined);
  useEffect(() => {
    if (state?.blob === blob && notifiedBlob.current !== blob) {
      notifiedBlob.current = blob;
      readyCallback.current?.();
    }
  }, [state, blob]);
  useEffect(() => {
    const control = new AbortController();
    let active = true;
    setState(undefined);
    const open = async () => {
      if (!sourceSha256) throw new Error("Exact source identity missing");
      const passive =
        blob.type === "application/vnd.wright.toolpaths+json"
          ? blob
          : await port.current?.(control.signal);
      if (
        !passive ||
        passive.type !== "application/vnd.wright.toolpaths+json" ||
        passive.size > 64 * 1024 * 1024
      )
        throw new Error("Supported bounded passive reader unavailable");
      const document = parseToolpaths(
        JSON.parse(await passive.text()),
        sourceSha256,
      );
      if (active) setState({ blob, document });
    };
    void open().catch(() => {
      if (active)
        setState({
          blob,
          error:
            "A complete toolpath preview is unavailable. Download the exact package and inspect it with a compatible engineering tool.",
        });
    });
    return () => {
      active = false;
      control.abort();
    };
  }, [blob, sourceSha256, available]);
  if (!state || state.blob !== blob)
    return <p role="status">Reading the exact layer paths…</p>;
  if (state.error) return <p role="status">{state.error}</p>;
  return state.document ? <ToolpathViewer document={state.document} /> : null;
}

/** Exact data with nearby plotting controls; axes remain explicit view choices. */
export function CsvNumericInspector({
  columns,
  rows,
}: {
  columns: readonly string[];
  rows: readonly (readonly string[])[];
}) {
  const [x, setX] = useState("");
  const [y, setY] = useState("");
  const [field, setField] = useState("");
  const numeric =
    columns.length <= 50 && rows.length <= 10_000
      ? columns
          .map((name, index) => ({ name, index }))
          .filter(
            ({ name, index }) =>
              columns.filter((column) => column === name).length === 1 &&
              rows.length > 0 &&
              rows.every(
                (row) =>
                  row[index]?.trim() !== "" &&
                  Number.isFinite(Number(row[index])),
              ),
          )
      : [];
  const selected = (name: string) =>
    numeric.find((item) => item.name === name)?.index;
  const xi = selected(x),
    yi = selected(y),
    vi = selected(field);
  const canPlot =
    xi !== undefined &&
    yi !== undefined &&
    vi !== undefined &&
    x !== y &&
    x !== field &&
    y !== field;
  return (
    <>
      {numeric.length >= 3 && (
        <details>
          <summary>View numerical samples</summary>
          <div className="wp-row">
            {[
              { title: "Horizontal column", value: x, change: setX },
              { title: "Vertical column", value: y, change: setY },
              { title: "Value column", value: field, change: setField },
            ].map((item) => (
              <label key={item.title}>
                {item.title}
                <select
                  value={item.value}
                  onChange={(event) => item.change(event.target.value)}
                >
                  <option value="">Choose a recorded column</option>
                  {numeric.map(({ name }) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          </div>
          {canPlot ? (
            <ScalarFieldPlot
              points={rows.map((row) => ({
                x: Number(row[xi]),
                y: Number(row[yi]),
                value: Number(row[vi]),
              }))}
              xLabel={x}
              yLabel={y}
              valueLabel={field}
              title="Recorded field samples"
            />
          ) : (
            <p role="status">
              Choose three distinct recorded numeric columns to view their
              samples.
            </p>
          )}
          <p className="wp-muted">
            Samples are projected onto the selected axes. Other coordinates
            remain in the exact table; no interpolated geometry or engineering
            acceptance is implied.
          </p>
        </details>
      )}
      <DataTable columns={columns} rows={rows} pageSize={10} />
    </>
  );
}
