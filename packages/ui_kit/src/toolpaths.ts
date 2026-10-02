/** Format-level view data. It is not slicer acceptance or a provider attestation. */
export type ToolpathSegment = readonly [number, number, number, number];
export interface ToolpathLayer {
  readonly index: number;
  readonly z: number;
  readonly model: readonly ToolpathSegment[];
  readonly support: readonly ToolpathSegment[];
  readonly unclassified: readonly ToolpathSegment[];
}
export interface ToolpathDocument {
  readonly packageSha256: string;
  readonly layers: readonly ToolpathLayer[];
  readonly classificationKnown: boolean;
  readonly provenance?: ToolpathReaderProvenance;
}
export interface ToolpathReaderProvenance {
  readonly reader: string;
  readonly sourceSha256: string;
  readonly archiveEntry: string | null;
  readonly method: string;
  readonly segments: number;
  readonly extrudingArcs: number;
  readonly arcMaximumChordErrorMm: number;
  readonly excludedUnlayeredCommands: number;
  readonly unclassifiedFeatures: readonly string[];
}

export function parseToolpaths(
  value: unknown,
  expectedPackageSha256: string,
): ToolpathDocument {
  const failure = () => {
    throw new Error(
      "Toolpaths do not match a supported finite package representation.",
    );
  };
  if (!value || typeof value !== "object" || Array.isArray(value))
    return failure();
  const data = value as Record<string, unknown>;
  if (
    data.format !== "wright.gcode.toolpaths.v1" ||
    !/^[0-9a-f]{64}$/.test(expectedPackageSha256) ||
    data.package_sha256 !== expectedPackageSha256 ||
    !Array.isArray(data.layers) ||
    !data.layers.length ||
    data.layers.length > 10000
  )
    return failure();
  const known = data.classification_source === "gcode_feature_comments";
  let total = 0,
    previous = -1;
  function segments(items: unknown): ToolpathSegment[] {
    if (items === undefined) return [];
    if (!Array.isArray(items) || total + items.length > 1_000_000)
      return failure();
    total += items.length;
    return items.map((item) => {
      if (
        !Array.isArray(item) ||
        item.length !== 4 ||
        item.some(
          (coordinate) =>
            typeof coordinate !== "number" ||
            !Number.isFinite(coordinate) ||
            Math.abs(coordinate) > 1_000_000,
        )
      )
        return failure();
      return [item[0], item[1], item[2], item[3]] as const;
    });
  }
  const layers = data.layers.map((item) => {
    if (!item || typeof item !== "object" || Array.isArray(item))
      return failure();
    const layer = item as Record<string, unknown>;
    if (
      typeof layer.index !== "number" ||
      !Number.isInteger(layer.index) ||
      layer.index <= previous ||
      typeof layer.z !== "number" ||
      !Number.isFinite(layer.z) ||
      Math.abs(layer.z) > 1_000_000
    )
      return failure();
    previous = layer.index;
    const model = segments(layer.model),
      support = segments(layer.support),
      unclassified = segments(layer.unclassified);
    return {
      index: layer.index,
      z: layer.z,
      model: known ? model : [],
      support: known ? support : [],
      unclassified: known
        ? unclassified
        : [...unclassified, ...model, ...support],
    };
  });
  if (!total) return failure();
  let provenance: ToolpathReaderProvenance | undefined;
  if (data.provenance !== undefined) {
    if (
      !data.provenance ||
      typeof data.provenance !== "object" ||
      Array.isArray(data.provenance)
    )
      return failure();
    const raw = data.provenance as Record<string, unknown>;
    const count = (value: unknown, maximum: number): value is number =>
      typeof value === "number" &&
      Number.isInteger(value) &&
      value >= 0 &&
      value <= maximum;
    const entry = raw.archive_entry;
    if (
      raw.reader !== "wright.passive-representations/1" ||
      raw.units !== "mm" ||
      raw.engineering_acceptance !== false ||
      typeof raw.source_sha256 !== "string" ||
      !/^[0-9a-f]{64}$/.test(raw.source_sha256) ||
      (entry !== null &&
        (typeof entry !== "string" ||
          entry.length > 1024 ||
          !entry ||
          /[\\:\u0000-\u001f]/.test(entry) ||
          entry.startsWith("/") ||
          entry
            .split("/")
            .some((part) => !part || part === "." || part === ".."))) ||
      (entry === null && raw.source_sha256 !== expectedPackageSha256) ||
      typeof raw.method !== "string" ||
      raw.method.length > 512 ||
      raw.segments !== total ||
      !count(raw.extruding_arcs, total) ||
      typeof raw.arc_maximum_chord_error_mm !== "number" ||
      !Number.isFinite(raw.arc_maximum_chord_error_mm) ||
      raw.arc_maximum_chord_error_mm <= 0 ||
      raw.arc_maximum_chord_error_mm > 0.02 ||
      !count(raw.unlayered_extrusion_commands_excluded, 2_000_000) ||
      !Array.isArray(raw.unclassified_features) ||
      raw.unclassified_features.length > 256 ||
      raw.unclassified_features.some(
        (item) => typeof item !== "string" || item.length > 256,
      )
    )
      return failure();
    provenance = {
      reader: raw.reader,
      sourceSha256: raw.source_sha256,
      archiveEntry: entry as string | null,
      method: raw.method,
      segments: total,
      extrudingArcs: raw.extruding_arcs,
      arcMaximumChordErrorMm: raw.arc_maximum_chord_error_mm,
      excludedUnlayeredCommands: raw.unlayered_extrusion_commands_excluded,
      unclassifiedFeatures: raw.unclassified_features as string[],
    };
  }
  return {
    packageSha256: expectedPackageSha256,
    layers,
    classificationKnown: known,
    ...(provenance ? { provenance } : {}),
  };
}
