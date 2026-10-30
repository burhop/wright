import { useEffect, useMemo, useRef, useState } from "react";
import { mcpService, type CapabilityView } from "../../services/mcp-service";
import { capabilitySetupGuides } from "../../services/provider-setup-guides";
import { ProviderSetupGuide } from "../../components/workspace/ProviderSetupGuide";

type Requirement = Record<string, unknown>;

/** Read-only setup information; the registry and run readiness own all decisions. */
export function TemplateToolSetup({
  requirements,
}: {
  requirements: Requirement[];
}) {
  const ids = useMemo(
    () =>
      [
        ...new Set(
          requirements.flatMap((item) =>
            Array.isArray(item.catalog_ids)
              ? item.catalog_ids.filter(
                  (id): id is string =>
                    typeof id === "string" &&
                    /^[a-z0-9][a-z0-9-]{0,127}$/.test(id),
                )
              : [],
          ),
        ),
      ].slice(0, 32),
    [requirements],
  );
  const [tools, setTools] = useState<Record<string, CapabilityView>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState("");
  const generation = useRef(0);

  useEffect(() => {
    const current = ++generation.current;
    setTools({});
    setErrors({});
    setChecking("");
    setLoading(true);
    void Promise.all(
      ids.map(async (id) => {
        try {
          const tool = await mcpService.getCapability(id);
          if (tool.capability_id !== id)
            throw new Error(
              "The catalog returned a different tool. Reopen setup.",
            );
          if (generation.current === current)
            setTools((items) => ({ ...items, [id]: tool }));
        } catch (reason) {
          if (generation.current === current)
            setErrors((items) => ({
              ...items,
              [id]:
                reason instanceof Error
                  ? reason.message
                  : "Tool setup information is unavailable.",
            }));
        }
      }),
    ).finally(() => {
      if (generation.current === current) setLoading(false);
    });
    return () => {
      ++generation.current;
    };
  }, [ids]);

  if (!ids.length) return null;
  const check = async (id: string) => {
    const current = generation.current;
    setChecking(id);
    setErrors((items) => ({ ...items, [id]: "" }));
    try {
      const observed = await mcpService.observeCapability(id);
      if (generation.current === current)
        setTools((items) => ({
          ...items,
          [id]: { ...items[id], compatibility: observed.compatibility },
        }));
    } catch (reason) {
      if (generation.current === current)
        setErrors((items) => ({
          ...items,
          [id]:
            reason instanceof Error
              ? reason.message
              : "The setup check could not finish.",
        }));
    } finally {
      if (generation.current === current) setChecking("");
    }
  };

  const needsSetup = Object.values(tools).filter(
    (tool) =>
      tool.compatibility.status !== "compatible" ||
      !tool.user_state.installed ||
      tool.user_state.explicit_disabled,
  ).length;
  const status = loading
    ? "Reading setup information…"
    : Object.values(errors).some(Boolean)
      ? "Some tool setup could not be checked"
      : needsSetup
        ? `${needsSetup} tool${needsSetup === 1 ? "" : "s"} need setup on this computer`
        : "Review tools · run readiness still required";
  return (
    <section
      className="engineering-template-dialog__readiness"
      aria-label="Tools on this computer"
    >
      <details>
        <summary>{status}</summary>
        <h4>Tools on this computer</h4>
        <p>
          Check the required setup before creating your workflow. This does not
          install tools or start engineering work.
        </p>
        {loading && <p role="status">Reading current tool setup…</p>}
        <table className="template-tool-setup">
          <thead>
            <tr>
              <th>Tool</th>
              <th>Setup</th>
              <th>Next step</th>
            </tr>
          </thead>
          <tbody>
            {ids.map((id) => {
              const tool = tools[id];
              const status = !tool
                ? "Not checked"
                : tool.compatibility.status !== "compatible"
                  ? "Needs attention"
                  : !tool.user_state.installed
                    ? "Not installed"
                    : tool.user_state.explicit_disabled
                      ? "Disabled"
                      : "Check run readiness";
              return (
                <tr key={id}>
                  <td>{tool?.name ?? id}</td>
                  <td>
                    {status}
                    {tool && (
                      <small>
                        {tool.compatibility.platform_key.replaceAll("_", " ")}
                      </small>
                    )}
                  </td>
                  <td>
                    <a
                      href={`/tool-registry?curation=all&search=${encodeURIComponent(id)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Open tool setup ↗
                    </a>
                    {tool && (
                      <button
                        type="button"
                        disabled={!!checking}
                        onClick={() => void check(id)}
                      >
                        {checking === id ? "Checking…" : "Check this computer"}
                      </button>
                    )}
                    {errors[id] && <p role="alert">{errors[id]}</p>}
                    {tool && (
                      <details>
                        <summary>Requirements and recovery</summary>
                        <p>
                          {tool.requirements.host_software?.join(", ") ||
                            (tool.locality === "remote"
                              ? "Hosted service; check access requirements."
                              : "Review this tool's setup requirements.")}
                        </p>
                        {tool.compatibility.reasons.map((reason, index) => (
                          <div key={`${reason.code}-${index}`}>
                            <p>{reason.message}</p>
                            <p>{reason.recovery}</p>
                          </div>
                        ))}
                        {tool.curation?.limitations.map((limit) => (
                          <p key={limit}>{limit}</p>
                        ))}
                        {capabilitySetupGuides[id] && (
                          <ProviderSetupGuide
                            text={capabilitySetupGuides[id]}
                          />
                        )}
                      </details>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p>
          These are setup candidates, not selected workflow bindings. Inputs,
          other capabilities and run readiness are checked before execution.
        </p>
      </details>
    </section>
  );
}
