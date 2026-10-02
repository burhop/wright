import { useEffect, useId, useRef, useState } from "react";
import type {
  ArtifactRef,
  InputBinding,
  InputDefinition,
  JsonValue,
} from "@wright/process-client";
import { assertContract } from "@wright/process-client";

export type ValueSchema = Readonly<Record<string, JsonValue>>;
const schemaKeys = new Set([
  "$schema",
  "$defs",
  "$ref",
  "type",
  "title",
  "description",
  "default",
  "enum",
  "const",
  "properties",
  "required",
  "additionalProperties",
  "items",
  "minItems",
  "maxItems",
  "uniqueItems",
  "minProperties",
  "maxProperties",
  "minimum",
  "maximum",
  "exclusiveMinimum",
  "exclusiveMaximum",
  "multipleOf",
  "minLength",
  "maxLength",
  "format",
]);
function record(value: unknown): value is Record<string, JsonValue> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}
function resolve(
  schema: ValueSchema,
  root: ValueSchema,
  depth = 0,
): ValueSchema | null {
  if (
    schema.$schema &&
    schema.$schema !== "https://json-schema.org/draft/2020-12/schema"
  )
    return null;
  if (depth > 24 || Object.keys(schema).some((key) => !schemaKeys.has(key)))
    return null;
  if (typeof schema.$ref === "string") {
    const definitions = root.$defs;
    if (!schema.$ref.startsWith("#/$defs/") || !record(definitions))
      return null;
    const target = definitions[schema.$ref.slice(8)];
    return record(target) ? resolve(target, root, depth + 1) : null;
  }
  if (
    record(schema.properties) &&
    Object.values(schema.properties).some(
      (child) => !record(child) || !resolve(child, root, depth + 1),
    )
  )
    return null;
  if (
    schema.items &&
    (!record(schema.items) || !resolve(schema.items, root, depth + 1))
  )
    return null;
  if (
    schema.type &&
    ![
      "string",
      "number",
      "integer",
      "boolean",
      "object",
      "array",
      "null",
    ].includes(String(schema.type))
  )
    return null;
  return schema;
}
function label(value: JsonValue): string {
  return typeof value === "string" ? value : JSON.stringify(value);
}
function JsonEditor({
  id,
  title,
  value,
  onChange,
  disabled,
}: {
  id: string;
  title: string;
  value?: JsonValue;
  onChange: (value?: JsonValue) => void;
  disabled?: boolean;
}) {
  const serialized = value === undefined ? "" : JSON.stringify(value, null, 2);
  const [draft, setDraft] = useState(serialized);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!error) setDraft(serialized);
  }, [serialized, error]);
  return (
    <>
      <label htmlFor={id}>{title}</label>
      <textarea
        id={id}
        value={draft}
        disabled={disabled}
        aria-invalid={!!error}
        onChange={(event) => {
          const text = event.target.value;
          setDraft(text);
          if (!text.trim()) {
            setError("");
            onChange(undefined);
            return;
          }
          try {
            const parsed = assertContract("JsonValue", JSON.parse(text));
            setError("");
            onChange(parsed);
          } catch {
            setError("Provide a finite JSON value within 64 KiB.");
            onChange(undefined);
          }
        }}
      />
      {error && <p role="alert">{error}</p>}
    </>
  );
}
export function SchemaField({
  schema,
  value,
  title,
  onChange,
  disabled = false,
  required = false,
  root = schema,
  level = 0,
}: {
  schema: ValueSchema;
  value?: JsonValue;
  title: string;
  onChange: (value?: JsonValue) => void;
  disabled?: boolean;
  required?: boolean;
  root?: ValueSchema;
  level?: number;
}) {
  const id = useId();
  const selected = resolve(schema, root);
  if (!selected || level > 24)
    return (
      <div className="wp-notice" role="status">
        {title}: unsupported schema. Open the input in its producing block or
        configure a supported editor.
      </div>
    );
  const name = `${title}${required ? " (required)" : ""}`;
  if (Array.isArray(selected.enum))
    return (
      <div className="wp-field">
        <label htmlFor={id}>{name}</label>
        <select
          id={id}
          disabled={disabled}
          value={
            value === undefined
              ? ""
              : String(
                  selected.enum.findIndex(
                    (item) => JSON.stringify(item) === JSON.stringify(value),
                  ),
                )
          }
          onChange={(event) =>
            onChange(
              event.target.value === ""
                ? undefined
                : (selected.enum as JsonValue[])[Number(event.target.value)],
            )
          }
        >
          <option value="">Choose a value</option>
          {selected.enum.map((item, index) => (
            <option key={index} value={index}>
              {label(item)}
            </option>
          ))}
        </select>
      </div>
    );
  if ("const" in selected || selected.type === "null")
    return (
      <div className="wp-field">
        <span>{name}</span>
        <p>
          Declared value:{" "}
          {label(selected.type === "null" ? null : selected.const)}
        </p>
        <button
          type="button"
          className="wp-link"
          disabled={disabled}
          onClick={() =>
            onChange(selected.type === "null" ? null : selected.const)
          }
        >
          Use declared value
        </button>
      </div>
    );
  if (selected.type === "object" && record(selected.properties)) {
    const objectValue = record(value) ? value : {};
    return (
      <fieldset className="wp-fieldset" disabled={disabled}>
        <legend>{name}</legend>
        {Object.entries(selected.properties)
          .slice(0, 256)
          .map(([key, child]) => (
            <SchemaField
              key={key}
              schema={child as ValueSchema}
              root={root}
              level={level + 1}
              title={
                record(child) && typeof child.title === "string"
                  ? child.title
                  : key
              }
              required={
                Array.isArray(selected.required) &&
                selected.required.includes(key)
              }
              value={
                Object.hasOwn(objectValue, key) ? objectValue[key] : undefined
              }
              onChange={(next) => {
                const entries = Object.entries(objectValue).filter(
                  ([field]) => field !== key,
                );
                if (next !== undefined) entries.push([key, next]);
                onChange(Object.fromEntries(entries));
              }}
            />
          ))}
      </fieldset>
    );
  }
  if (selected.type === "array" && record(selected.items)) {
    const entries = Array.isArray(value) ? value : [];
    return (
      <fieldset className="wp-fieldset" disabled={disabled}>
        <legend>{name}</legend>
        {entries.slice(0, 256).map((entry, index) => (
          <div key={index}>
            <SchemaField
              title={`Item ${index + 1}`}
              schema={selected.items as ValueSchema}
              root={root}
              level={level + 1}
              value={entry}
              onChange={(next) =>
                onChange(
                  next === undefined
                    ? entries.filter((_, position) => position !== index)
                    : entries.map((item, position) =>
                        position === index ? next : item,
                      ),
                )
              }
            />
            <button
              type="button"
              className="wp-link"
              onClick={() =>
                onChange(entries.filter((_, position) => position !== index))
              }
            >
              Remove item {index + 1}
            </button>
          </div>
        ))}
        <p className="wp-muted">Add items using the declared item schema.</p>
        <JsonEditor
          id={id}
          title="Array values"
          value={value}
          disabled={disabled}
          onChange={(next) => onChange(next)}
        />
      </fieldset>
    );
  }
  if (selected.type === "boolean")
    return (
      <div className="wp-field">
        <label htmlFor={id}>
          <input
            id={id}
            type="checkbox"
            disabled={disabled}
            checked={value === true}
            onChange={(event) => onChange(event.target.checked)}
          />
          {name}
        </label>
        {value === undefined && (
          <p className="wp-muted">
            Not provided.{" "}
            <button
              type="button"
              className="wp-link"
              disabled={disabled}
              onClick={() => onChange(false)}
            >
              Use false
            </button>
          </p>
        )}
      </div>
    );
  if (selected.type === "string")
    return (
      <div className="wp-field">
        <label htmlFor={id}>{name}</label>
        <textarea
          id={id}
          disabled={disabled}
          value={typeof value === "string" ? value : ""}
          maxLength={
            typeof selected.maxLength === "number"
              ? selected.maxLength
              : undefined
          }
          onChange={(event) => onChange(event.target.value)}
        />
        {typeof selected.description === "string" && (
          <p className="wp-muted">{selected.description}</p>
        )}
      </div>
    );
  if (selected.type === "number" || selected.type === "integer")
    return (
      <div className="wp-field">
        <label htmlFor={id}>{name}</label>
        <input
          id={id}
          type="number"
          disabled={disabled}
          value={typeof value === "number" ? value : ""}
          min={
            typeof selected.minimum === "number" ? selected.minimum : undefined
          }
          max={
            typeof selected.maximum === "number" ? selected.maximum : undefined
          }
          step={
            typeof selected.multipleOf === "number"
              ? selected.multipleOf
              : selected.type === "integer"
                ? 1
                : "any"
          }
          onChange={(event) => {
            const parsed =
              event.target.value === ""
                ? undefined
                : Number(event.target.value);
            onChange(
              parsed !== undefined && Number.isFinite(parsed)
                ? parsed
                : undefined,
            );
          }}
        />
      </div>
    );
  return (
    <div className="wp-field">
      <JsonEditor
        id={id}
        title={name}
        value={value}
        disabled={disabled}
        onChange={onChange}
      />
    </div>
  );
}
export function ImageThumbnail({ blob, title }: { blob: Blob; title: string }) {
  const [stored, setStored] = useState<{ blob: Blob; url: string }>();
  const [failed, setFailed] = useState<Blob>();
  useEffect(() => {
    if (
      !["image/png", "image/jpeg", "image/webp", "image/gif"].includes(
        blob.type,
      ) ||
      blob.size > 32 * 1024 * 1024
    )
      return;
    const value = URL.createObjectURL(blob);
    setStored({ blob, url: value });
    return () => {
      URL.revokeObjectURL(value);
    };
  }, [blob]);
  const url = stored?.blob === blob ? stored.url : "";
  return url && failed !== blob ? (
    <img
      className="wp-thumbnail"
      src={url}
      alt={title}
      onError={() => setFailed(blob)}
    />
  ) : (
    <p className="wp-muted">A bitmap preview is unavailable.</p>
  );
}
export function InputEditor({
  definition,
  binding,
  onChange,
  onUpload,
  preview,
  disabled = false,
  now = Date.now(),
}: {
  definition: InputDefinition;
  binding?: InputBinding | null;
  onChange: (binding: InputBinding | null) => void;
  onUpload?: (file: File, definition: InputDefinition) => Promise<ArtifactRef>;
  preview?: Blob;
  disabled?: boolean;
  now?: number;
}) {
  const id = useId();
  const supplied =
    binding === undefined
      ? (definition.current_value ?? definition.default)
      : binding;
  // Owning schemas may omit default discriminators. Preserve their actual
  // prepared values/references rather than displaying them as missing inputs.
  const current = supplied
    ? "reference" in supplied
      ? { ...supplied, kind: "file" as const }
      : "option_id" in supplied
        ? { ...supplied, kind: "option" as const }
        : { ...supplied, kind: "value" as const }
    : supplied;
  const [file, setFile] = useState<File>();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const generation = useRef(0);
  useEffect(
    () => () => {
      generation.current++;
    },
    [],
  );
  const title = `${definition.title}${definition.unit ? ` · ${definition.unit}` : ""}${definition.frame ? ` · ${definition.frame}` : ""}`;
  if (definition.binding_kind === "file")
    return (
      <div className="wp-field">
        <label htmlFor={id}>
          {title}
          {definition.required ? " (required)" : ""}
        </label>
        <input
          id={id}
          type="file"
          disabled={disabled || uploading || !onUpload}
          onChange={async (event) => {
            const selected = event.target.files?.[0];
            const active = ++generation.current;
            if (!selected) return;
            setFile(selected);
            setError("");
            onChange(null);
            if (selected.size > 32 * 1024 * 1024) {
              setError("Choose a file smaller than 32 MiB.");
              onChange(null);
              return;
            }
            if (!onUpload) return;
            setUploading(true);
            try {
              const reference = await onUpload(selected, definition);
              if (active === generation.current)
                onChange({
                  kind: "file",
                  input_id: definition.input_id,
                  reference,
                  provenance: "supplied",
                });
            } catch {
              if (active === generation.current) {
                setError(
                  "The file could not be prepared. Try uploading it again.",
                );
                onChange(null);
              }
            } finally {
              if (active === generation.current) setUploading(false);
            }
          }}
        />
        {uploading && <p role="status">Preparing file…</p>}
        {error && <p role="alert">{error}</p>}
        {(file || preview) && (
          <ImageThumbnail
            blob={file || preview!}
            title={file ? `Selected reference: ${file.name}` : definition.title}
          />
        )}
        {current?.kind === "file" && (
          <p className="wp-muted">{current.reference.artifact_ref}</p>
        )}
        {!onUpload && (
          <p className="wp-muted">File upload is unavailable in this view.</p>
        )}
      </div>
    );
  if (definition.binding_kind === "option") {
    const validTime =
      definition.options_observed_at &&
      Number.isFinite(Date.parse(definition.options_observed_at));
    const stale =
      !!definition.options_stale_after &&
      (!Number.isFinite(Date.parse(definition.options_stale_after)) ||
        Date.parse(definition.options_stale_after) <= now);
    const available =
      !!definition.option_source &&
      !!validTime &&
      !!definition.available_options?.length &&
      !stale;
    return (
      <div className="wp-field">
        <label htmlFor={id}>
          {title}
          {definition.required ? " (required)" : ""}
        </label>
        <select
          id={id}
          disabled={disabled || !available}
          value={current?.kind === "option" ? current.option_id : ""}
          onChange={(event) => {
            const option = definition.available_options?.find(
              (item) => item.option_id === event.target.value,
            );
            onChange(
              option && available
                ? {
                    kind: "option",
                    input_id: definition.input_id,
                    option_id: option.option_id,
                    value: option.value,
                    capability: definition.option_source!,
                    observed_at: definition.options_observed_at!,
                    stale_after: definition.options_stale_after,
                    provenance: "supplied",
                  }
                : null,
            );
          }}
        >
          <option value="">Choose an available option</option>
          {(definition.available_options ?? []).map((option) => (
            <option key={option.option_id} value={option.option_id}>
              {option.title}
            </option>
          ))}
        </select>
        {!available && (
          <p className="wp-muted">
            {stale
              ? "The configured choices need refreshing."
              : "The configured choices are unavailable."}
          </p>
        )}
      </div>
    );
  }
  return (
    <SchemaField
      schema={definition.value_schema}
      title={title}
      required={definition.required}
      disabled={disabled}
      value={current?.kind === "value" ? current.value : undefined}
      onChange={(value) =>
        onChange(
          value === undefined
            ? null
            : {
                kind: "value",
                input_id: definition.input_id,
                value,
                provenance: "supplied",
              },
        )
      }
    />
  );
}
