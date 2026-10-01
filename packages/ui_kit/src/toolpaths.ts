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
  return {
    packageSha256: expectedPackageSha256,
    layers,
    classificationKnown: known,
  };
}
