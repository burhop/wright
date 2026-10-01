import { useEffect, useState } from "react";
import type { JsonValue } from "@wright/process-client";
import { ImageThumbnail } from "./inputs";
import { ThreeDViewer } from "./geometry";

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
                    {typeof cell === "string" ? cell : JSON.stringify(cell)}
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
        `${40 + ((x - minX) / (maxX - minX || 1)) * 510},${260 - ((y - minY) / (maxY - minY || 1)) * 220}`,
    )
    .join(" ");
  return (
    <figure className="wp-plot">
      <figcaption>{title}</figcaption>
      <svg
        viewBox="0 0 600 310"
        role="img"
        aria-label={`${title}; ${xLabel} from ${minX} to ${maxX}; ${yLabel} from ${minY} to ${maxY}`}
      >
        <path d="M40 30V260H560" fill="none" stroke="currentColor" />
        <polyline
          points={coordinates}
          fill="none"
          stroke="var(--color-secondary)"
          strokeWidth="2"
        />
        <text x="300" y="298" textAnchor="middle" fill="currentColor">
          {xLabel}
        </text>
        <text
          x="12"
          y="145"
          transform="rotate(-90 12 145)"
          textAnchor="middle"
          fill="currentColor"
        >
          {yLabel}
        </text>
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
        viewBox="0 0 600 310"
        role="img"
        aria-label={`${title}; ${valueLabel} samples from ${minV} to ${maxV}; ${xLabel}; ${yLabel}`}
      >
        <path d="M40 30V260H560" fill="none" stroke="currentColor" />
        {points.map((point, index) => (
          <circle
            key={index}
            cx={40 + ((point.x - minX) / (maxX - minX || 1)) * 510}
            cy={260 - ((point.y - minY) / (maxY - minY || 1)) * 220}
            r={3}
            fill={`hsl(${240 * (1 - (point.value - minV) / (maxV - minV || 1))} 75% 50%)`}
          >
            <title>{`${xLabel}: ${point.x}; ${yLabel}: ${point.y}; ${valueLabel}: ${point.value}`}</title>
          </circle>
        ))}
        <text x="300" y="298" textAnchor="middle" fill="currentColor">
          {xLabel}
        </text>
        <text
          x="12"
          y="145"
          transform="rotate(-90 12 145)"
          textAnchor="middle"
          fill="currentColor"
        >
          {yLabel}
        </text>
      </svg>
      <p>
        {valueLabel}: {minV}–{maxV}
      </p>
      <p className="wp-muted">
        Supplied samples without interpolated geometry. Review the exact
        assessment for acceptance.
      </p>
    </figure>
  );
}
export function RepresentationViewer({
  blob,
  title,
}: {
  blob: Blob;
  title: string;
}) {
  const [data, setData] = useState<{
    blob: Blob;
    text?: string;
    bytes?: ArrayBuffer;
  }>();
  const [error, setError] = useState<{ blob: Blob; message: string }>();
  const type = blob.type.split(";")[0];
  useEffect(() => {
    let active = true;
    setData(undefined);
    setError(undefined);
    if (["image/png", "image/jpeg", "image/gif", "image/webp"].includes(type))
      return;
    const maximum = [
      "model/stl",
      "application/sla",
      "application/vnd.ms-pki.stl",
    ].includes(type)
      ? 32 * 1024 * 1024
      : type === "text/csv"
        ? 2 * 1024 * 1024
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
        ? blob.text().then((text) => ({ text }))
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
  }, [blob, type]);
  if (["image/png", "image/jpeg", "image/gif", "image/webp"].includes(type))
    return <ImageThumbnail blob={blob} title={title} />;
  if (error?.blob === blob) return <p role="status">{error.message}</p>;
  if (!data || data.blob !== blob)
    return <p role="status">Opening representation…</p>;
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
      return <DataTable {...table} />;
    } catch {
      return (
        <p role="status">
          A bounded table preview is unavailable. Download the complete CSV.
        </p>
      );
    }
  }
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
