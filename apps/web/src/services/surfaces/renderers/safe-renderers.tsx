import DOMPurify from "dompurify";

export interface SafeDisplayRepresentation {
  readonly mediaType: string;
  readonly encoding: "utf-8" | "base64" | "json";
  readonly data: unknown;
  readonly activeHtml?: boolean;
  readonly metadata?: Readonly<Record<string, unknown>>;
  readonly fallbackRank?: number;
}

interface Props {
  readonly representation: SafeDisplayRepresentation;
  readonly description: string;
}

function requireString(value: unknown, label: string): string {
  if (typeof value !== "string") throw new TypeError(`${label} must be text`);
  return value;
}

function requireTable(value: unknown): {
  columns: readonly string[];
  data: readonly (readonly unknown[])[];
} {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError("table data must be an object");
  }
  const table = value as Record<string, unknown>;
  const columns = table.columns;
  const data = table.data;
  if (
    !Array.isArray(columns) ||
    !columns.every((item) => typeof item === "string") ||
    !Array.isArray(data) ||
    !data.every((row) => Array.isArray(row) && row.length === columns.length)
  ) {
    throw new TypeError("table columns and rows are malformed");
  }
  return {
    columns: columns as string[],
    data: data as unknown[][],
  };
}

function safeCell(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (["string", "number", "boolean"].includes(typeof value)) {
    return String(value);
  }
  return JSON.stringify(value);
}

export function SafeRepresentationRenderer({
  representation,
  description,
}: Props) {
  switch (representation.mediaType) {
    case "text/plain":
      if (representation.encoding !== "utf-8") {
        throw new TypeError("text representation must use utf-8");
      }
      return (
        <pre role="region" aria-label={description}>
          {requireString(representation.data, "text data")}
        </pre>
      );
    case "application/vnd.wright.table+json": {
      if (representation.encoding !== "json") {
        throw new TypeError("table representation must use JSON");
      }
      const table = requireTable(representation.data);
      return (
        <table aria-label={description}>
          <caption>{description}</caption>
          <thead>
            <tr>
              {table.columns.map((column, index) => (
                <th key={`${index}:${column}`} scope="col">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.data.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, columnIndex) => (
                  <td key={columnIndex}>{safeCell(cell)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
    }
    case "image/png":
    case "image/jpeg": {
      if (representation.encoding !== "base64") {
        throw new TypeError("raster representation must use base64");
      }
      const data = requireString(representation.data, "raster data");
      return (
        <img
          src={`data:${representation.mediaType};base64,${data}`}
          alt={description}
          draggable={false}
          decoding="async"
        />
      );
    }
    case "image/svg+xml": {
      if (representation.encoding !== "utf-8") {
        throw new TypeError("SVG representation must use utf-8");
      }
      const sanitized = DOMPurify.sanitize(
        requireString(representation.data, "SVG data"),
        { USE_PROFILES: { svg: true, svgFilters: true } },
      );
      return (
        <div
          role="img"
          aria-label={description}
          dangerouslySetInnerHTML={{ __html: sanitized }}
        />
      );
    }
    case "text/html": {
      if (representation.activeHtml) {
        throw new TypeError(
          "active HTML requires the isolated active renderer",
        );
      }
      if (representation.encoding !== "utf-8") {
        throw new TypeError("HTML representation must use utf-8");
      }
      const sanitized = DOMPurify.sanitize(
        requireString(representation.data, "HTML data"),
        { USE_PROFILES: { html: true } },
      );
      return (
        <div
          role="document"
          aria-label={description}
          data-wright-document-locked="true"
          dangerouslySetInnerHTML={{ __html: sanitized }}
        />
      );
    }
    default:
      throw new TypeError(
        `Safe display renderer does not support ${representation.mediaType}`,
      );
  }
}
