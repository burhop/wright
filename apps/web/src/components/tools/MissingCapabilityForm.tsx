import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  mcpService,
  type MissingCapabilityReport,
  type MissingCapabilitySearchContext,
} from "../../services/mcp-service";

const DOMAINS = [
  "cad",
  "ecad",
  "fea",
  "cfd",
  "cam",
  "grasshopper",
  "3d-printing",
  "slicing",
  "python",
  "other",
];

export function MissingCapabilityForm({
  isOpen,
  searchContext,
  onClose,
  onSubmitted,
}: {
  isOpen: boolean;
  searchContext: MissingCapabilitySearchContext;
  onClose: () => void;
  onSubmitted?: (report: MissingCapabilityReport) => void;
}) {
  const [name, setName] = useState("");
  const [vendor, setVendor] = useState("Unknown");
  const [sourceUrl, setSourceUrl] = useState("");
  const [domain, setDomain] = useState(searchContext.filters.domain || "cad");
  const [expectedTask, setExpectedTask] = useState("");
  const [platform, setPlatform] = useState("");
  const [hostApplication, setHostApplication] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState<MissingCapabilityReport | null>(
    null,
  );
  const idempotencyKey = useRef(
    `missing-capability-${Date.now()}-${Math.random()}`,
  );
  const titleRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (isOpen) {
      setDomain(searchContext.filters.domain || "cad");
      setError(null);
      setSubmitted(null);
      idempotencyKey.current = `missing-capability-${Date.now()}-${Math.random()}`;
      window.setTimeout(() => titleRef.current?.focus(), 0);
    }
  }, [isOpen, searchContext]);

  if (!isOpen) return null;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const report = await mcpService.reportMissingCapability(
        {
          name: name.trim(),
          vendor: vendor.trim() || "Unknown",
          source_url: sourceUrl.trim() || undefined,
          domains: [domain],
          expected_task: expectedTask.trim(),
          platform: platform.trim() || undefined,
          host_application: hostApplication.trim() || undefined,
          notes: notes.trim() || undefined,
          search_context: searchContext,
        },
        idempotencyKey.current,
      );
      setSubmitted(report);
      onSubmitted?.(report);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The missing-capability report could not be saved.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="missing-capability-title"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 200,
        display: "grid",
        placeItems: "center",
        padding: "var(--space-lg)",
        background: "color-mix(in srgb, var(--color-primary) 45%, transparent)",
      }}
    >
      <section
        style={{
          width: "min(680px, 100%)",
          maxHeight: "90vh",
          overflowY: "auto",
          padding: "var(--space-xl)",
          borderRadius: "var(--radius-lg)",
          background: "var(--color-neutral)",
          boxShadow: "var(--shadow-elevated)",
        }}
      >
        <div
          style={{ display: "flex", justifyContent: "space-between", gap: 16 }}
        >
          <h2 id="missing-capability-title" ref={titleRef} tabIndex={-1}>
            Report a missing capability
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close missing capability form"
          >
            Close
          </button>
        </div>
        <p>
          This creates a review request only. It cannot install a server or add
          an entry to Wright&apos;s trusted catalog.
        </p>
        <p data-testid="missing-capability-search-context">
          Search context: {searchContext.query || "No search text"}
          {Object.entries(searchContext.filters)
            .filter(([, value]) => value)
            .map(([key, value]) => ` · ${key}: ${value}`)}
        </p>

        {submitted ? (
          <div role="status">
            <h3>Report saved</h3>
            <p>
              Reference {submitted.report_id}. Its state is {submitted.state};
              it is not an installable capability.
            </p>
            <button type="button" onClick={onClose}>
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={submit} style={{ display: "grid", gap: 12 }}>
            <label>
              Capability or MCP name
              <input
                required
                maxLength={200}
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </label>
            <label>
              Vendor or publisher
              <input
                required
                maxLength={200}
                value={vendor}
                onChange={(event) => setVendor(event.target.value)}
              />
            </label>
            <label>
              Public source URL
              <input
                type="url"
                maxLength={2048}
                value={sourceUrl}
                onChange={(event) => setSourceUrl(event.target.value)}
              />
            </label>
            <label>
              Engineering domain
              <select
                value={domain}
                onChange={(event) => setDomain(event.target.value)}
              >
                {DOMAINS.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
            <label>
              What engineering task should it perform?
              <textarea
                required
                maxLength={2000}
                value={expectedTask}
                onChange={(event) => setExpectedTask(event.target.value)}
              />
            </label>
            <label>
              Required platform
              <input
                maxLength={200}
                value={platform}
                onChange={(event) => setPlatform(event.target.value)}
                placeholder="For example, Windows 11 x64"
              />
            </label>
            <label>
              Host application
              <input
                maxLength={200}
                value={hostApplication}
                onChange={(event) => setHostApplication(event.target.value)}
                placeholder="For example, Solid Edge"
              />
            </label>
            <label>
              Notes
              <textarea
                maxLength={4000}
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
              />
            </label>
            {error && <p role="alert">{error}</p>}
            <button type="submit" disabled={submitting}>
              {submitting ? "Saving report…" : "Submit review request"}
            </button>
          </form>
        )}
      </section>
    </div>
  );
}
