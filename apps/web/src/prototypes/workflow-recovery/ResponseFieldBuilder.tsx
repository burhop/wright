type ObjectValue = Record<string, unknown>;
const objectValue = (value: unknown): ObjectValue | null =>
  value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as ObjectValue)
    : null;

function fieldKind(field: unknown): string | null {
  const value = objectValue(field);
  if (!value || value.$ref || value.const !== undefined) return null;
  if (value.enum !== undefined)
    return value.type === "string" &&
      Array.isArray(value.enum) &&
      value.enum.every((choice) => typeof choice === "string")
      ? "choice"
      : null;
  return ["string", "number", "integer", "boolean"].includes(String(value.type))
    ? String(value.type)
    : null;
}

/** Edit the declared answer shape. Runtime values and decisions belong to the backend. */
export function ResponseFieldBuilder({
  schema,
  disabled,
  onChange,
  onError,
}: {
  schema: unknown;
  disabled: boolean;
  onChange: (schema: ObjectValue) => void;
  onError: (message: string) => void;
}) {
  const current = objectValue(schema);
  const properties = objectValue(current?.properties);
  if (
    !current ||
    current.type !== "object" ||
    (current.properties !== undefined && !properties) ||
    current.$ref
  )
    return (
      <p>
        Use Advanced declaration to edit this response schema. Its existing
        structure is preserved.
      </p>
    );
  const fields = properties ?? {};
  const required = Array.isArray(current.required) ? current.required : [];
  const update = (name: string, patch: ObjectValue) => {
    if (disabled) return;
    onChange({
      ...current,
      properties: {
        ...fields,
        [name]: { ...objectValue(fields[name]), ...patch },
      },
    });
  };
  const remove = (name: string) => {
    if (disabled) return;
    const remaining = { ...fields };
    delete remaining[name];
    onChange({
      ...current,
      properties: remaining,
      required: required.filter((key) => key !== name),
    });
  };
  const changeKind = (name: string, kind: string) => {
    if (disabled) return;
    const value = { ...objectValue(fields[name]) };
    // A deliberate type change drops constraints/defaults for the previous type.
    for (const key of [
      "enum",
      "default",
      "minLength",
      "maxLength",
      "format",
      "minimum",
      "maximum",
      "exclusiveMinimum",
      "exclusiveMaximum",
      "multipleOf",
    ])
      delete value[key];
    value.type = kind === "choice" ? "string" : kind;
    if (kind === "choice") value.enum = ["First choice", "Second choice"];
    onChange({ ...current, properties: { ...fields, [name]: value } });
  };
  return (
    <section className="recovery-response-fields" aria-label="Answer fields">
      <h4>Answer fields</h4>
      <p>
        Choose what the user should provide. Include units in the label or help
        text, for example Width (mm).
      </p>
      {Object.entries(fields).map(([name, item], index) => {
        const value = objectValue(item);
        const kind = fieldKind(item);
        if (!kind || !value)
          return (
            <fieldset key={index} disabled={disabled}>
              <legend>
                {typeof value?.title === "string" ? value.title : name}
              </legend>
              <p>
                This field uses an advanced schema. Edit its declaration below;
                it will be preserved when other fields change.
              </p>
              <button
                type="button"
                className="recovery-button recovery-button--quiet"
                onClick={() => remove(name)}
              >
                Remove field {name}
              </button>
            </fieldset>
          );
        return (
          <fieldset key={index} disabled={disabled}>
            <legend>Field {index + 1}</legend>
            <label>
              Field name
              <input
                value={name}
                onChange={(event) => {
                  const next = event.target.value;
                  if (disabled) return;
                  if (next !== name && Object.hasOwn(fields, next)) {
                    onError("Each answer field needs a different name.");
                    return;
                  }
                  const renamed = Object.fromEntries(
                    Object.entries(fields).map(([key, field]) => [
                      key === name ? next : key,
                      field,
                    ]),
                  );
                  onChange({
                    ...current,
                    properties: renamed,
                    required: required.map((key) =>
                      key === name ? next : key,
                    ),
                  });
                }}
              />
            </label>
            <label>
              Field label
              <input
                value={typeof value.title === "string" ? value.title : ""}
                placeholder={name}
                onChange={(event) =>
                  update(name, { title: event.target.value })
                }
              />
            </label>
            <label>
              Answer type
              <select
                value={kind}
                onChange={(event) => changeKind(name, event.target.value)}
              >
                <option value="string">Text</option>
                <option value="number">Number</option>
                <option value="integer">Whole number</option>
                <option value="choice">Choice</option>
                <option value="boolean">Yes or no</option>
              </select>
            </label>
            <label>
              Help text / units
              <input
                value={
                  typeof value.description === "string" ? value.description : ""
                }
                onChange={(event) =>
                  update(name, { description: event.target.value })
                }
              />
            </label>
            {kind === "choice" && (
              <label>
                Choices (one per line)
                <textarea
                  rows={3}
                  value={(value.enum as string[]).join("\n")}
                  onChange={(event) =>
                    update(name, { enum: event.target.value.split("\n") })
                  }
                />
              </label>
            )}
            {(kind === "number" || kind === "integer") &&
              (["minimum", "maximum"] as const).map((key) => (
                <label key={key}>
                  {key === "minimum" ? "Minimum value" : "Maximum value"}
                  <input
                    type="number"
                    step="any"
                    value={
                      typeof value[key] === "number" ? String(value[key]) : ""
                    }
                    onChange={(event) => {
                      if (disabled) return;
                      const changed = { ...value };
                      if (!event.target.value) delete changed[key];
                      else if (Number.isFinite(Number(event.target.value)))
                        changed[key] = Number(event.target.value);
                      onChange({
                        ...current,
                        properties: { ...fields, [name]: changed },
                      });
                    }}
                  />
                </label>
              ))}
            <label className="recovery-response-fields__required">
              <input
                type="checkbox"
                checked={required.includes(name)}
                onChange={(event) => {
                  if (disabled) return;
                  onChange({
                    ...current,
                    required: event.target.checked
                      ? [...required.filter((key) => key !== name), name]
                      : required.filter((key) => key !== name),
                  });
                }}
              />
              Required answer
            </label>
            <button
              type="button"
              className="recovery-button recovery-button--quiet"
              onClick={() => remove(name)}
            >
              Remove field {name}
            </button>
          </fieldset>
        );
      })}
      {!Object.keys(fields).length && (
        <p>
          No answer fields yet. Add the information this step should request.
        </p>
      )}
      <button
        type="button"
        className="recovery-button recovery-button--secondary"
        disabled={disabled || Object.keys(fields).length >= 256}
        onClick={() => {
          if (disabled) return;
          let name = "answer";
          for (let suffix = 2; Object.hasOwn(fields, name); suffix += 1)
            name = `answer_${suffix}`;
          onChange({
            ...current,
            properties: { ...fields, [name]: { type: "string", title: "" } },
            required: [...required, name],
          });
        }}
      >
        Add answer field
      </button>
    </section>
  );
}
