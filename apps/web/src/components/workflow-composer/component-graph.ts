import type {
  DraftBlockProjection,
  DraftComponentConceptKind,
  DraftComponentProjection,
  DraftProjection,
} from "./draft-projection";

export interface DraftComponentScope {
  readonly componentInstanceId: string;
  readonly componentId: string;
  readonly componentVersion: string;
  readonly internalSemanticId: string;
}

export interface DraftComponentState {
  readonly instanceSemanticId: string;
  readonly component: DraftComponentProjection;
  readonly collapsed: boolean;
  readonly internalAddressCount: number;
  readonly targetedInternalSemanticIds: readonly string[];
}

const PATH_ROOTS: Record<DraftComponentConceptKind, string> = {
  block: "blocks/",
  port: "ports/",
  relationship: "relationships/",
  artifact_contract: "artifact-contracts/",
  binding: "bindings/",
  component: "components/",
};

function allBlocks(
  projection: DraftProjection,
): readonly DraftBlockProjection[] {
  return projection.phases.flatMap((phase) => phase.blocks);
}

export function validateComponentProjection(
  projection: DraftProjection,
): readonly string[] {
  const errors: string[] = [];
  const componentIds = new Set<string>();
  for (const component of projection.components) {
    if (componentIds.has(component.semanticId)) {
      errors.push(`WORKFLOW_COMPONENT_ID_DUPLICATE:${component.semanticId}`);
    }
    componentIds.add(component.semanticId);
    if (!/^sha256:[a-f0-9]{64}$/.test(component.internalDefinitionDigest)) {
      errors.push(`WORKFLOW_COMPONENT_DIGEST_INVALID:${component.semanticId}`);
    }
    if (component.internalAddresses.length === 0) {
      errors.push(
        `WORKFLOW_COMPONENT_INTERNAL_ADDRESS_EMPTY:${component.semanticId}`,
      );
    }
    const semanticIds = new Set<string>();
    const paths = new Set<string>();
    for (const address of component.internalAddresses) {
      if (!address.semanticId.startsWith(`${component.semanticId}.`)) {
        errors.push(
          `WORKFLOW_COMPONENT_INTERNAL_ADDRESS_SCOPE_INVALID:${address.semanticId}`,
        );
      }
      if (
        !address.relativePath.startsWith(PATH_ROOTS[address.conceptKind]) ||
        address.relativePath
          .split("/")
          .some((segment) => segment === "." || segment === "..")
      ) {
        errors.push(
          `WORKFLOW_COMPONENT_INTERNAL_ADDRESS_PATH_INVALID:${address.relativePath}`,
        );
      }
      if (
        semanticIds.has(address.semanticId) ||
        paths.has(address.relativePath)
      ) {
        errors.push(
          `WORKFLOW_COMPONENT_INTERNAL_ADDRESS_DUPLICATE:${component.semanticId}`,
        );
      }
      semanticIds.add(address.semanticId);
      paths.add(address.relativePath);
    }
  }
  for (const block of allBlocks(projection)) {
    if (
      block.componentRef !== null &&
      block.componentRef !== undefined &&
      !componentIds.has(block.componentRef.componentId)
    ) {
      errors.push(
        `WORKFLOW_COMPONENT_REFERENCE_UNRESOLVED:${block.semanticId}`,
      );
    }
  }
  return Object.freeze(errors);
}

export function resolveComponentScope(
  projection: DraftProjection,
  componentInstanceId: string,
  internalSemanticId: string,
): DraftComponentScope {
  if (validateComponentProjection(projection).length > 0) {
    throw new Error("WORKFLOW_COMPONENT_PROJECTION_INVALID");
  }
  const instance = allBlocks(projection).find(
    (block) => block.semanticId === componentInstanceId,
  );
  if (instance?.componentRef === null || instance?.componentRef === undefined) {
    throw new Error(
      `WORKFLOW_COMPONENT_INSTANCE_MISSING:${componentInstanceId}`,
    );
  }
  const component = projection.components.find(
    (item) => item.semanticId === instance.componentRef?.componentId,
  );
  if (component === undefined)
    throw new Error(
      `WORKFLOW_COMPONENT_REFERENCE_MISSING:${instance.componentRef.componentId}`,
    );
  if (
    !component.internalAddresses.some(
      (address) => address.semanticId === internalSemanticId,
    )
  ) {
    throw new Error(
      `WORKFLOW_COMPONENT_INTERNAL_ADDRESS_MISSING:${internalSemanticId}`,
    );
  }
  return Object.freeze({
    componentInstanceId,
    componentId: component.semanticId,
    componentVersion: component.version,
    internalSemanticId,
  });
}

export function projectComponentStates(
  projection: DraftProjection,
  collapsedInstanceIds: ReadonlySet<string>,
  targetScopes: readonly DraftComponentScope[] = [],
): readonly DraftComponentState[] {
  if (validateComponentProjection(projection).length > 0) {
    throw new Error("WORKFLOW_COMPONENT_PROJECTION_INVALID");
  }
  return Object.freeze(
    allBlocks(projection).flatMap((block) => {
      if (block.componentRef === null || block.componentRef === undefined)
        return [];
      const component = projection.components.find(
        (item) => item.semanticId === block.componentRef?.componentId,
      );
      if (component === undefined) return [];
      return [
        Object.freeze({
          instanceSemanticId: block.semanticId,
          component,
          collapsed: collapsedInstanceIds.has(block.semanticId),
          internalAddressCount: component.internalAddresses.length,
          targetedInternalSemanticIds: Object.freeze(
            targetScopes
              .filter(
                (scope) =>
                  scope.componentInstanceId === block.semanticId &&
                  scope.componentId === component.semanticId,
              )
              .map((scope) => scope.internalSemanticId)
              .sort(),
          ),
        }),
      ];
    }),
  );
}

export function graphDetailLevel(blockCount: number): "detailed" | "compact" {
  return blockCount > 25 ? "compact" : "detailed";
}

export function findBlockByIdentity(
  projection: DraftProjection,
  query: string,
): DraftBlockProjection | null {
  const normalized = query.trim().toLocaleLowerCase();
  if (normalized.length === 0) return null;
  const blocks = [...allBlocks(projection)].sort((left, right) =>
    left.semanticId.localeCompare(right.semanticId),
  );
  return (
    blocks.find(
      (block) => block.semanticId.toLocaleLowerCase() === normalized,
    ) ??
    blocks.find((block) => block.title.toLocaleLowerCase() === normalized) ??
    blocks.find(
      (block) =>
        block.semanticId.toLocaleLowerCase().includes(normalized) ||
        block.title.toLocaleLowerCase().includes(normalized),
    ) ??
    null
  );
}
