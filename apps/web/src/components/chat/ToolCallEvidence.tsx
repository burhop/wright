import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ToolCallEvidence as Evidence } from "../../store/types";

const cellStyle = {
  padding: "6px 10px",
  verticalAlign: "top" as const,
  textAlign: "left" as const,
};

function decodeValue(text: string): unknown {
  if (text.length > 256 * 1024) return text;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export function ReadableToolValue({
  value,
  depth = 0,
}: {
  value: unknown;
  depth?: number;
}) {
  if (value === null || value === undefined)
    return <span>No value returned.</span>;
  if (Array.isArray(value)) {
    if (!value.length) return <span>No items returned.</span>;
    if (depth >= 4)
      return (
        <span>{value.length} items; full data is in the saved record.</span>
      );
    return (
      <>
        <ol style={{ margin: 0, paddingLeft: 20 }}>
          {value.slice(0, 40).map((item, index) => (
            <li key={index}>
              <ReadableToolValue value={item} depth={depth + 1} />
            </li>
          ))}
        </ol>
        {value.length > 40 && (
          <small>
            Showing 40 of {value.length} items. Download the saved record for
            all items.
          </small>
        )}
      </>
    );
  }
  if (typeof value === "object") {
    const fields = Object.entries(value);
    if (!fields.length) return <span>No fields returned.</span>;
    if (depth >= 4)
      return (
        <span>{fields.length} fields; full data is in the saved record.</span>
      );
    return (
      <>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            tableLayout: "fixed",
          }}
        >
          <tbody>
            {fields.slice(0, 40).map(([key, item]) => (
              <tr key={key}>
                <th
                  scope="row"
                  style={{
                    ...cellStyle,
                    width: "35%",
                    color: "var(--color-secondary)",
                    overflowWrap: "anywhere",
                  }}
                >
                  {key}
                </th>
                <td style={{ ...cellStyle, overflowWrap: "anywhere" }}>
                  <ReadableToolValue value={item} depth={depth + 1} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {fields.length > 40 && (
          <small>
            Showing 40 of {fields.length} fields. Download the saved record for
            all fields.
          </small>
        )}
      </>
    );
  }
  if (typeof value !== "string") return <span>{String(value)}</span>;
  if (!value) return <span>No text returned.</span>;
  if (value.length > 2000)
    return (
      <>
        <div style={{ whiteSpace: "pre-wrap" }}>{value.slice(0, 2000)}</div>
        <small>
          Text preview: first 2,000 characters. Full text is in the saved
          record.
        </small>
      </>
    );
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      skipHtml
      urlTransform={(url) => (/^https?:\/\//i.test(url) ? url : "")}
      components={{
        img: ({ alt }) => (
          <span>
            {alt || "Image"} (image content is retained in the record)
          </span>
        ),
        a: ({ href, children }) => (
          <a href={href} target="_blank" rel="noopener noreferrer">
            {children}
          </a>
        ),
      }}
    >
      {value}
    </ReactMarkdown>
  );
}

function downloadRecord(record: Evidence) {
  const blob = new Blob([JSON.stringify(record, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `tool-call-${record.call_id.replace(/[^a-zA-Z0-9_.-]/g, "_")}.json`;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

function EvidenceRecord({
  record,
  single,
}: {
  record: Evidence;
  single: boolean;
}) {
  const [technicalOpen, setTechnicalOpen] = useState(false);
  const parts = record.tool_name.split("__");
  const name = parts[parts.length - 1].replace(/[_-]+/g, " ");
  const provider =
    parts.length > 1 ? parts[parts.length - 2].replace(/[_-]+/g, " ") : "";
  const recorded = record.response !== null;
  return (
    <details
      open={single}
      style={{
        marginTop: 8,
        borderTop: "1px solid var(--color-border)",
        paddingTop: 8,
      }}
    >
      <summary style={{ cursor: "pointer" }}>
        <strong>{name}</strong>
        {provider && <span> · {provider}</span>}
        <span style={{ marginLeft: 8, color: "var(--color-secondary)" }}>
          {recorded ? "Response recorded" : "Matched response unavailable"}
        </span>
      </summary>
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          tableLayout: "fixed",
        }}
      >
        <tbody>
          <tr>
            <th scope="row" style={{ ...cellStyle, width: "25%" }}>
              Arguments
            </th>
            <td style={cellStyle}>
              {record.arguments === null ? (
                "Not retained."
              ) : typeof record.arguments === "object" &&
                !Object.keys(record.arguments).length ? (
                "None."
              ) : (
                <ReadableToolValue value={record.arguments} />
              )}
            </td>
          </tr>
          <tr>
            <th scope="row" style={cellStyle}>
              Result
            </th>
            <td style={cellStyle}>
              {recorded ? (
                <ReadableToolValue
                  value={decodeValue(
                    record.display_response ?? record.response!,
                  )}
                />
              ) : (
                "No exact matching response is available in this history."
              )}
            </td>
          </tr>
          {record.timestamp > 0 && (
            <tr>
              <th scope="row" style={cellStyle}>
                Recorded
              </th>
              <td style={cellStyle}>
                {new Date(record.timestamp).toLocaleString()}
              </td>
            </tr>
          )}
        </tbody>
      </table>
      {record.record_note && <p>{record.record_note}</p>}
      <button type="button" onClick={() => downloadRecord(record)}>
        Download saved record
      </button>
      <details
        onToggle={(event) => setTechnicalOpen(event.currentTarget.open)}
        style={{ marginTop: 8 }}
      >
        <summary style={{ cursor: "pointer" }}>Technical details</summary>
        {technicalOpen && (
          <>
            <dl>
              <dt>Tool</dt>
              <dd style={{ overflowWrap: "anywhere" }}>{record.tool_name}</dd>
              <dt>Call ID</dt>
              <dd style={{ overflowWrap: "anywhere" }}>{record.call_id}</dd>
              <dt>Source</dt>
              <dd>{record.source}</dd>
              <dt>Request / response records</dt>
              <dd>
                {record.request_message_id ?? "Unavailable"} /{" "}
                {record.response_message_id ?? "Unavailable"}
              </dd>
            </dl>
            <pre
              style={{
                whiteSpace: "pre-wrap",
                overflowWrap: "anywhere",
                maxHeight: 300,
                overflow: "auto",
              }}
            >
              {record.response?.slice(0, 65536) ?? "No matched response."}
            </pre>
            {(record.response?.length ?? 0) > 65536 && (
              <small>
                First 65,536 characters shown. Download the saved record for the
                complete redacted response.
              </small>
            )}
          </>
        )}
      </details>
    </details>
  );
}

export function ToolCallEvidence({
  records,
  sessionId,
  forRequest = false,
}: {
  records: Evidence[];
  sessionId?: string;
  forRequest?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const scoped = records.filter(
    (record) => sessionId && record.session_id === sessionId,
  );
  if (!scoped.length) return null;
  return (
    <details
      data-testid="retained-tool-evidence"
      onToggle={(event) => setExpanded(event.currentTarget.open)}
      style={{
        width: "100%",
        padding: "10px 14px",
        boxSizing: "border-box",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-md)",
        background: "var(--color-surface-subtle)",
        fontSize: "0.8rem",
        overflowWrap: "anywhere",
      }}
    >
      <summary style={{ cursor: "pointer", color: "var(--color-secondary)" }}>
        Tools used {forRequest ? "for this request" : "in this answer"} (
        {scoped.length}) — inspect saved requests and results
      </summary>
      {expanded &&
        scoped.map((record) => (
          <EvidenceRecord
            key={record.call_id}
            record={record}
            single={scoped.length === 1}
          />
        ))}
    </details>
  );
}
