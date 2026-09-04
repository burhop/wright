import { useState } from "react";
import type {
  JsonSchema,
  NativeContract,
  NativeDocument,
  NativeStep,
} from "../../services/native-process";
import { newId, type NativeCommand } from "./model";
export interface StepBuffer {
  title: string;
  fields: Record<string, string>;
  present?: string[];
  error?: string;
}
export function stepBuffer(step: NativeStep): StepBuffer {
  const fields: Record<string, string> = {};
  for (const [key, value] of Object.entries(step.config)) {
    if (value && typeof value === "object" && !Array.isArray(value)) {
      fields[`${key}.value`] = value.value;
      fields[`${key}.unit`] = value.unit;
    } else
      fields[key] = Array.isArray(value)
        ? value.join("\n")
        : String(value ?? "");
  }
  return { title: step.title, fields, present: Object.keys(step.config) };
}
export function bufferConfig(
  buffer: StepBuffer,
  schema: JsonSchema,
): NativeStep["config"] {
  const config: NativeStep["config"] = {};
  for (const [key, field] of Object.entries(schema.properties ?? {})) {
    if (field.type === "object") {
      const value = buffer.fields[`${key}.value`] ?? "",
        unit = buffer.fields[`${key}.unit`] ?? "";
      if (value || unit) config[key] = { value, unit };
    } else {
      const value = buffer.fields[key] ?? "";
      if (
        value !== "" ||
        (field.type === "string" &&
          !field.enum &&
          buffer.present?.includes(key))
      )
        config[key] = field.type === "array" ? value.split("\n") : value;
    }
  }
  return config;
}
interface Props {
  document: NativeDocument;
  contract: NativeContract;
  selected: string | null;
  buffer?: StepBuffer;
  updateBuffer: (id: string, buffer: StepBuffer | null) => void;
  command: (command: NativeCommand) => boolean;
  select: (id: string | null) => void;
}
export function NativeInspector({
  document,
  contract,
  selected,
  buffer,
  updateBuffer,
  command,
  select,
}: Props) {
  const [deleting, setDeleting] = useState(false);
  const step = document.definition.steps.find((s) => s.id === selected);
  if (!step)
    return (
      <aside className="native-inspector" aria-label="Process inspector">
        <h2>Inspector</h2>
        <p>
          Select a step to configure its inputs and inspect exact connections.
        </p>
      </aside>
    );
  const operation = contract.operations.find((op) => op.id === step.operation);
  const current = buffer ?? stepBuffer(step);
  const ports = document.definition.ports.filter(
    (port) => port.step_id === step.id,
  );
  const portIds = new Set(ports.map((port) => port.id));
  const connections = document.definition.connections.filter(
    (c) => portIds.has(c.source_port_id) || portIds.has(c.target_port_id),
  );
  const outputs = document.definition.outputs.filter((output) =>
    portIds.has(output.port_id),
  );
  function field(key: string, value: string) {
    updateBuffer(step!.id, {
      ...current,
      fields: { ...current.fields, [key]: value },
      present: [...new Set([...(current.present ?? []), key.split(".")[0]])],
      error: undefined,
    });
  }
  const renderField = (key: string, schema: JsonSchema) => {
    const id = `native-config-${key}`,
      label =
        key.replaceAll("_", " ") +
        (operation?.required_config_keys.includes(key)
          ? " (needed for run)"
          : "");
    if (schema.type === "object")
      return (
        <fieldset key={key}>
          <legend>{label}</legend>
          <label>
            Exact value
            <input
              data-testid={`${id}-value`}
              value={current.fields[`${key}.value`] ?? ""}
              onChange={(e) => field(`${key}.value`, e.target.value)}
            />
          </label>
          <label>
            Unit
            <select
              data-testid={`${id}-unit`}
              value={current.fields[`${key}.unit`] ?? ""}
              onChange={(e) => field(`${key}.unit`, e.target.value)}
            >
              <option value="">Choose unit</option>
              {schema.properties?.unit.enum?.map((unit) => (
                <option key={String(unit)}>{String(unit)}</option>
              ))}
            </select>
          </label>
        </fieldset>
      );
    if (schema.enum)
      return (
        <label key={key}>
          {label}
          <select
            data-testid={id}
            value={current.fields[key] ?? ""}
            onChange={(e) => field(key, e.target.value)}
          >
            <option value="">Not configured</option>
            {schema.enum.map((value) => (
              <option key={String(value)}>{String(value)}</option>
            ))}
          </select>
        </label>
      );
    return (
      <label key={key}>
        {label}
        {schema.type === "array" ? " (one per line)" : ""}
        <textarea
          data-testid={id}
          rows={
            schema.type === "array" || (schema.maxLength ?? 0) > 200 ? 4 : 2
          }
          value={current.fields[key] ?? ""}
          onChange={(e) => field(key, e.target.value)}
        />
      </label>
    );
  };
  return (
    <aside
      className="native-inspector"
      aria-label="Step inspector"
      data-testid="native-inspector"
    >
      <h2>Inspector</h2>
      <p className="native-operation">{step.operation}</p>
      <p>
        <small>
          Step ID: <code>{step.id}</code>
        </small>
      </p>
      <label>
        Step title
        <input
          data-testid="native-step-title"
          readOnly={!operation}
          value={current.title}
          onChange={(e) =>
            updateBuffer(step.id, {
              ...current,
              title: e.target.value,
              error: undefined,
            })
          }
        />
      </label>
      {operation ? (
        <>
          {Object.entries(operation.config_schema.properties ?? {}).map(
            ([key, schema]) => renderField(key, schema),
          )}
          <p>
            <small>
              Blank fields remain unconfigured. Apply changes to update the
              process language.
            </small>
          </p>
          <div className="native-actions">
            <button
              data-testid="native-apply-step"
              onClick={() => {
                if (
                  command({
                    type: "step",
                    id: step.id,
                    title: current.title,
                    config: bufferConfig(current, operation.config_schema),
                  })
                )
                  updateBuffer(step.id, null);
              }}
            >
              Apply changes
            </button>
            {buffer && (
              <button
                data-testid="native-discard-fields"
                onClick={() => updateBuffer(step.id, null)}
              >
                Discard field changes
              </button>
            )}
          </div>
          {buffer && (
            <p role="status">
              Field changes are separate from the saved process until applied.
            </p>
          )}
        </>
      ) : (
        <p role="status">
          This operation is unsupported by this service. Its definition is
          preserved; execution requires a supported binding/version.
        </p>
      )}
      <h3>Exact ports</h3>
      <ul className="native-port-list">
        {ports.map((port) => (
          <li key={port.id}>
            <strong>{port.label}</strong> · {port.direction} · {port.type}
            <br />
            <code>{port.id}</code>
            {port.direction === "output" && port.type === "artifact" && (
              <label>
                <input
                  type="checkbox"
                  data-testid={`native-declare-${port.id}`}
                  checked={outputs.some((output) => output.port_id === port.id)}
                  onChange={(e) =>
                    command({
                      type: "output",
                      portId: port.id,
                      id: newId("output"),
                      title: `${step.title}: ${port.label}`,
                      enabled: e.target.checked,
                    })
                  }
                />
                Declare as process output
              </label>
            )}
          </li>
        ))}
      </ul>
      <h3>Connections ({connections.length})</h3>
      <ul className="native-port-list">
        {connections.map((connection) => (
          <li key={connection.id}>
            <code>{connection.source_port_id}</code> →{" "}
            <code>{connection.target_port_id}</code>
            <button
              data-testid={`native-remove-${connection.id}`}
              onClick={() =>
                command({ type: "remove-connection", id: connection.id })
              }
            >
              Remove connection
            </button>
          </li>
        ))}
      </ul>
      <button
        data-testid="native-review-delete"
        onClick={() => setDeleting(true)}
      >
        Review step deletion
      </button>
      {deleting && (
        <section className="native-warning" aria-label="Step deletion impact">
          <p>
            Delete “{step.title}” and its {ports.length} ports,{" "}
            {connections.length} connections and {outputs.length} declared
            outputs? Other steps remain. Undo restores the complete change.
          </p>
          <button
            data-testid="native-confirm-delete"
            onClick={() => {
              if (command({ type: "remove-step", id: step.id })) {
                updateBuffer(step.id, null);
                select(null);
                setDeleting(false);
              }
            }}
          >
            Delete step and connections
          </button>
          <button
            data-testid="native-cancel-delete"
            onClick={() => setDeleting(false)}
          >
            Keep step
          </button>
        </section>
      )}
    </aside>
  );
}
