import type {
  NativeContract,
  NativeDefinition,
  NativeDocument,
  NativeStep,
  Presentation,
  JsonSchema,
} from "../../services/native-process";

export function newId(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}
function validString(value: string) {
  if (
    value.normalize("NFC") !== value ||
    /[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(
      value,
    )
  )
    throw new Error(
      "Use normalized Unicode text without incomplete characters.",
    );
}
const encoder = new TextEncoder();
function compareUtf8(a: string, b: string) {
  const left = encoder.encode(a),
    right = encoder.encode(b);
  for (let i = 0; i < Math.min(left.length, right.length); i++)
    if (left[i] !== right[i]) return left[i] - right[i];
  return left.length - right.length;
}
/** Official semantic JSON representation. Layout, viewport and selection never enter this function. */
export function canonicalJson(value: unknown): string {
  if (value === null || typeof value === "boolean") return String(value);
  if (typeof value === "string") {
    validString(value);
    return JSON.stringify(value);
  }
  if (typeof value === "number") {
    if (!Number.isSafeInteger(value) || Object.is(value, -0))
      throw new Error("Only canonical safe integers are supported.");
    return String(value);
  }
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (typeof value === "object") {
    return `{${Object.keys(value)
      .sort(compareUtf8)
      .map((key) => {
        validString(key);
        return `${JSON.stringify(key)}:${canonicalJson((value as Record<string, unknown>)[key])}`;
      })
      .join(",")}}`;
  }
  throw new Error("Unsupported process value.");
}

/** Strict parser for conformance and simulated programmatic clients, never an alternate DSL. */
export function parseCanonicalInput(text: string): unknown {
  if (
    encoder.encode(text).length > 1024 * 1024 ||
    text.charCodeAt(0) === 0xfeff
  )
    throw new Error("Invalid process JSON size or encoding.");
  let offset = 0;
  const whitespace = () => {
    while (/[ \t\r\n]/.test(text[offset] ?? "") && offset < text.length)
      offset++;
  };
  function string(): string {
    const start = offset++;
    while (offset < text.length) {
      const token = text[offset++];
      if (token === "\\") offset++;
      else if (token === '"') {
        const value = JSON.parse(text.slice(start, offset)) as string;
        validString(value);
        return value;
      }
    }
    throw new Error("Unterminated JSON string.");
  }
  function value(depth: number): unknown {
    if (depth > 30) throw new Error("Process JSON nesting is too deep.");
    whitespace();
    const token = text[offset];
    if (token === '"') return string();
    if (token === "{") {
      offset++;
      whitespace();
      const result: Record<string, unknown> = Object.create(null) as Record<
        string,
        unknown
      >;
      if (text[offset] === "}") {
        offset++;
        return result;
      }
      while (offset < text.length) {
        whitespace();
        if (text[offset] !== '"') throw new Error("Expected an object key.");
        const key = string();
        if (Object.hasOwn(result, key))
          throw new Error("Duplicate process key.");
        whitespace();
        if (text[offset++] !== ":") throw new Error("Expected colon.");
        result[key] = value(depth + 1);
        whitespace();
        const delimiter = text[offset++];
        if (delimiter === "}") return result;
        if (delimiter !== ",") throw new Error("Expected object delimiter.");
      }
    }
    if (token === "[") {
      offset++;
      whitespace();
      const result: unknown[] = [];
      if (text[offset] === "]") {
        offset++;
        return result;
      }
      while (offset < text.length) {
        result.push(value(depth + 1));
        whitespace();
        const delimiter = text[offset++];
        if (delimiter === "]") return result;
        if (delimiter !== ",") throw new Error("Expected array delimiter.");
      }
    }
    for (const [literal, result] of [
      ["true", true],
      ["false", false],
      ["null", null],
    ] as const) {
      if (text.slice(offset, offset + literal.length) === literal) {
        offset += literal.length;
        return result;
      }
    }
    const match = /^-?(?:0|[1-9][0-9]*)(?=[,}\]\s]|$)/.exec(text.slice(offset));
    if (!match) throw new Error("Only integer JSON numbers are supported.");
    offset += match[0].length;
    const number = Number(match[0]);
    canonicalJson(number);
    return number;
  }
  const result = value(0);
  whitespace();
  if (offset !== text.length)
    throw new Error("Unexpected trailing process JSON.");
  return result;
}

/** Bounded subset used by the published v1 schema; backend validation remains authoritative. */
export function schemaError(
  value: unknown,
  schema: JsonSchema,
  root = schema,
  path = "definition",
): string | null {
  if (schema.$ref) {
    const name = schema.$ref.replace("#/$defs/", "");
    const target = root.$defs?.[name];
    return target
      ? schemaError(value, target, root, path)
      : `${path}: unsupported schema reference.`;
  }
  const fail = (message: string) => `${path}: ${message}`;
  if ("const" in schema && value !== schema.const)
    return fail("unsupported value.");
  if (schema.enum && !schema.enum.includes(value))
    return fail("choose a supported value.");
  if (
    schema.oneOf &&
    schema.oneOf.filter((s) => !schemaError(value, s, root, path)).length !== 1
  )
    return fail("value does not match the process language.");
  if (schema.allOf)
    for (const sub of schema.allOf) {
      const error = schemaError(value, sub, root, path);
      if (error) return error;
    }
  if (schema.if && !schemaError(value, schema.if, root, path) && schema.then) {
    const error = schemaError(value, schema.then, root, path);
    if (error) return error;
  }
  if (schema.type === "null" && value !== null) return fail("expected null.");
  if (schema.type === "boolean" && typeof value !== "boolean")
    return fail("expected true or false.");
  if (
    schema.type === "integer" &&
    (typeof value !== "number" ||
      !Number.isSafeInteger(value) ||
      Object.is(value, -0))
  )
    return fail("expected a safe integer.");
  if (
    typeof value === "number" &&
    ((schema.minimum !== undefined && value < schema.minimum) ||
      (schema.maximum !== undefined && value > schema.maximum))
  )
    return fail("number is outside the supported range.");
  if (schema.type === "string" && typeof value !== "string")
    return fail("expected text.");
  if (typeof value === "string") {
    if (
      (schema.minLength !== undefined &&
        [...value].length < schema.minLength) ||
      (schema.maxLength !== undefined && [...value].length > schema.maxLength)
    )
      return fail("text length is outside the supported range.");
    if (schema.pattern && !new RegExp(schema.pattern, "u").test(value))
      return fail("text has an invalid format.");
  }
  if (schema.type === "array" && !Array.isArray(value))
    return fail("expected a list.");
  if (Array.isArray(value)) {
    if (
      (schema.minItems !== undefined && value.length < schema.minItems) ||
      (schema.maxItems !== undefined && value.length > schema.maxItems)
    )
      return fail("list length is outside the supported range.");
    if (
      schema.uniqueItems &&
      new Set(value.map((v) => canonicalJson(v))).size !== value.length
    )
      return fail("list contains duplicates.");
    if (schema.items)
      for (let i = 0; i < value.length; i++) {
        const error = schemaError(
          value[i],
          schema.items,
          root,
          `${path}[${i}]`,
        );
        if (error) return error;
      }
  }
  if (
    schema.type === "object" &&
    (!value || typeof value !== "object" || Array.isArray(value))
  )
    return fail("expected a record.");
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const record = value as Record<string, unknown>,
      keys = Object.keys(record);
    if (
      schema.maxProperties !== undefined &&
      keys.length > schema.maxProperties
    )
      return fail("too many fields.");
    for (const key of schema.required ?? [])
      if (!(key in record)) return fail(`missing ${key}.`);
    for (const key of keys) {
      if (schema.propertyNames) {
        const error = schemaError(key, schema.propertyNames, root, path);
        if (error) return error;
      }
      const prop = schema.properties?.[key];
      if (prop) {
        const error = schemaError(record[key], prop, root, `${path}.${key}`);
        if (error) return error;
      } else if (schema.additionalProperties === false)
        return fail(`unknown field ${key}.`);
      else if (typeof schema.additionalProperties === "object") {
        const error = schemaError(
          record[key],
          schema.additionalProperties,
          root,
          `${path}.${key}`,
        );
        if (error) return error;
      }
    }
  }
  return null;
}

export function validateDocument(
  document: NativeDocument,
  contract: NativeContract,
): void {
  const definition = document.definition;
  if (
    contract.format !== "wright-native-process" ||
    contract.schema_version !== "1.0.0"
  )
    throw new Error(
      "This editor does not support the service's process language version.",
    );
  if (encoder.encode(canonicalJson(definition)).length > 1024 * 1024)
    throw new Error("The process exceeds 1 MiB.");
  const error = schemaError(definition, contract.schema);
  if (error) throw new Error(error);
  const entities = [
    definition,
    ...definition.steps,
    ...definition.ports,
    ...definition.connections,
    ...definition.outputs,
  ];
  if (new Set(entities.map((entity) => entity.id)).size !== entities.length)
    throw new Error("Process identities must be globally unique.");
  const steps = new Map(definition.steps.map((step) => [step.id, step]));
  const ports = new Map(definition.ports.map((port) => [port.id, port]));
  const keys = new Set<string>();
  for (const port of ports.values()) {
    if (!steps.has(port.step_id))
      throw new Error("Every port must belong to an existing step.");
    const key = `${port.step_id}/${port.direction}/${port.key}`;
    if (keys.has(key))
      throw new Error("Port keys must be unique within a step and direction.");
    keys.add(key);
    const descriptor = contract.operations.find(
      (op) => op.id === steps.get(port.step_id)!.operation,
    );
    if (descriptor) {
      const signature = (
        port.direction === "input" ? descriptor.inputs : descriptor.outputs
      ).find((p) => p.key === port.key);
      if (
        !signature ||
        signature.type !== port.type ||
        signature.cardinality !== port.cardinality ||
        signature.required !== port.required
      )
        throw new Error(
          "The port does not match its operation's published signature.",
        );
    }
  }
  const incoming = new Set<string>(),
    pairs = new Set<string>(),
    graph = new Map<string, string[]>();
  for (const connection of definition.connections) {
    const source = ports.get(connection.source_port_id),
      target = ports.get(connection.target_port_id);
    if (!source || !target)
      throw new Error("A connection endpoint no longer exists.");
    if (source.direction !== "output" || target.direction !== "input")
      throw new Error("Connect an output port to an input port.");
    if (
      source.type !== target.type ||
      source.cardinality !== target.cardinality
    )
      throw new Error("Port types and cardinalities must match exactly.");
    if (source.step_id === target.step_id)
      throw new Error("A step cannot connect to itself.");
    if (target.cardinality === "one" && incoming.has(target.id))
      throw new Error("This input already has a connection. Remove it first.");
    const pair = `${source.id}/${target.id}`;
    if (pairs.has(pair))
      throw new Error("This exact connection already exists.");
    incoming.add(target.id);
    pairs.add(pair);
    graph.set(source.step_id, [
      ...(graph.get(source.step_id) ?? []),
      target.step_id,
    ]);
  }
  const visiting = new Set<string>(),
    visited = new Set<string>();
  function visit(id: string) {
    if (visiting.has(id))
      throw new Error("This connection would create a cycle.");
    if (visited.has(id)) return;
    visiting.add(id);
    for (const next of graph.get(id) ?? []) visit(next);
    visiting.delete(id);
    visited.add(id);
  }
  for (const step of definition.steps) visit(step.id);
  for (const output of definition.outputs) {
    const port = ports.get(output.port_id);
    if (!port || port.direction !== "output" || port.type !== "artifact")
      throw new Error("Declared outputs must refer to artifact output ports.");
  }
  if (Object.keys(document.presentation).length > 100)
    throw new Error("Too many layout positions.");
  for (const [id, point] of Object.entries(document.presentation)) {
    if (
      !steps.has(id) ||
      Object.keys(point).sort().join(",") !== "x,y" ||
      !Number.isSafeInteger(point.x) ||
      !Number.isSafeInteger(point.y) ||
      Math.abs(point.x) > 100000 ||
      Math.abs(point.y) > 100000
    )
      throw new Error("Invalid step position.");
  }
  // Decimal lexical checks supplement the schema's intentionally broader pattern.
  for (const step of definition.steps)
    for (const value of Object.values(step.config)) {
      if (value && typeof value === "object" && !Array.isArray(value)) {
        const decimal = value.value,
          digits = decimal.replace(/[-.]/g, "").replace(/^0+/, "");
        const plain = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?$/.test(decimal);
        const [whole, fraction = ""] = decimal.replace(/^-/, "").split(".");
        const beyondLimit =
          plain &&
          (BigInt(whole) > 1000000000000000000n ||
            (BigInt(whole) === 1000000000000000000n && fraction !== ""));
        if (!plain || decimal === "-0" || digits.length > 34 || beyondLimit)
          throw new Error(
            "Use an exact decimal without exponent, leading zeroes or trailing fractional zeroes.",
          );
      }
    }
}
export type NativeCommand =
  | { type: "add-step"; operation: string; id: string; title: string }
  | { type: "step"; id: string; title: string; config: NativeStep["config"] }
  | { type: "title"; title: string }
  | { type: "connect"; id: string; source: string; target: string }
  | { type: "remove-connection"; id: string }
  | { type: "remove-step"; id: string }
  | { type: "position"; id: string; x: number; y: number }
  | {
      type: "output";
      portId: string;
      id: string;
      title: string;
      enabled: boolean;
    };
export function applyCommand(
  current: NativeDocument,
  command: NativeCommand,
  contract: NativeContract,
): NativeDocument {
  const next = structuredClone(current),
    definition = next.definition;
  switch (command.type) {
    case "add-step": {
      const operation = contract.operations.find(
        (op) => op.id === command.operation,
      );
      if (!operation)
        throw new Error("Choose an operation supported by this service.");
      definition.steps.push({
        id: command.id,
        title: command.title,
        operation: operation.id,
        config: {},
      });
      for (const direction of ["input", "output"] as const)
        for (const port of direction === "input"
          ? operation.inputs
          : operation.outputs) {
          definition.ports.push({
            ...port,
            id: newId("port"),
            step_id: command.id,
            direction,
            label: port.label ?? port.key,
          });
        }
      next.presentation[command.id] = {
        x: ((definition.steps.length - 1) % 3) * 300,
        y: Math.floor((definition.steps.length - 1) / 3) * 220,
      };
      break;
    }
    case "title":
      definition.title = command.title;
      break;
    case "step": {
      const step = definition.steps.find((s) => s.id === command.id);
      if (!step) throw new Error("Step no longer exists.");
      step.title = command.title;
      step.config = command.config;
      break;
    }
    case "connect":
      definition.connections.push({
        id: command.id,
        source_port_id: command.source,
        target_port_id: command.target,
      });
      break;
    case "remove-connection":
      definition.connections = definition.connections.filter(
        (c) => c.id !== command.id,
      );
      break;
    case "remove-step": {
      const removed = new Set(
        definition.ports
          .filter((port) => port.step_id === command.id)
          .map((port) => port.id),
      );
      definition.steps = definition.steps.filter(
        (step) => step.id !== command.id,
      );
      definition.ports = definition.ports.filter(
        (port) => !removed.has(port.id),
      );
      definition.connections = definition.connections.filter(
        (c) => !removed.has(c.source_port_id) && !removed.has(c.target_port_id),
      );
      definition.outputs = definition.outputs.filter(
        (output) => !removed.has(output.port_id),
      );
      delete next.presentation[command.id];
      break;
    }
    case "position":
      next.presentation[command.id] = {
        x: Math.round(command.x),
        y: Math.round(command.y),
      };
      break;
    case "output":
      definition.outputs = definition.outputs.filter(
        (output) => output.port_id !== command.portId,
      );
      if (command.enabled)
        definition.outputs.push({
          id: command.id,
          port_id: command.portId,
          title: command.title,
        });
      break;
  }
  validateDocument(next, contract);
  return next;
}
export interface NativeHistory {
  present: NativeDocument;
  past: NativeDocument[];
  future: NativeDocument[];
}
export function pushCommand(
  history: NativeHistory,
  command: NativeCommand,
  contract: NativeContract,
): NativeHistory {
  const next = applyCommand(history.present, command, contract);
  if (canonicalJson(next) === canonicalJson(history.present)) return history;
  return {
    present: next,
    past: [...history.past.slice(-49), history.present],
    future: [],
  };
}
export function undo(history: NativeHistory): NativeHistory {
  const previous = history.past.at(-1);
  return previous
    ? {
        present: previous,
        past: history.past.slice(0, -1),
        future: [history.present, ...history.future],
      }
    : history;
}
export function redo(history: NativeHistory): NativeHistory {
  const next = history.future[0];
  return next
    ? {
        present: next,
        past: [...history.past, history.present],
        future: history.future.slice(1),
      }
    : history;
}
export function emptyDocument(): NativeDocument {
  return {
    definition: {
      format: "wright-native-process",
      schema_version: "1.0.0",
      id: newId("process"),
      title: "Untitled process",
      steps: [],
      ports: [],
      connections: [],
      outputs: [],
    },
    presentation: {},
  };
}
export function defaultPresentation(
  definition: NativeDefinition,
): Presentation {
  return Object.fromEntries(
    definition.steps.map((step, index) => [
      step.id,
      { x: (index % 3) * 300, y: Math.floor(index / 3) * 220 },
    ]),
  );
}
