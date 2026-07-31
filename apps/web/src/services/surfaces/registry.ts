import type { SurfaceDescriptor } from "./surface-contract";

export interface SurfacePresenter {
  mount(container: HTMLElement): void | Promise<void>;
  update(descriptor: SurfaceDescriptor): void | Promise<void>;
  dispose(): void;
}

export interface SurfacePresenterContribution {
  readonly id: string;
  readonly sourceKinds: readonly SurfaceDescriptor["source"]["kind"][];
  readonly priority: number;
  canPresent?(descriptor: SurfaceDescriptor): boolean;
  create(descriptor: SurfaceDescriptor): SurfacePresenter;
}

export interface DisposableRegistration {
  dispose(): void;
}

export class SurfacePresenterRegistry {
  private readonly contributions = new Map<
    string,
    SurfacePresenterContribution
  >();

  register(contribution: SurfacePresenterContribution): DisposableRegistration {
    if (this.contributions.has(contribution.id)) {
      throw new Error(
        `Surface presenter is already registered: ${contribution.id}`,
      );
    }
    this.contributions.set(contribution.id, contribution);
    let active = true;
    return {
      dispose: () => {
        if (active) {
          active = false;
          this.contributions.delete(contribution.id);
        }
      },
    };
  }

  resolve(descriptor: SurfaceDescriptor): SurfacePresenterContribution | null {
    return (
      [...this.contributions.values()]
        .filter(
          (candidate) =>
            candidate.sourceKinds.includes(descriptor.source.kind) &&
            (candidate.canPresent?.(descriptor) ?? true),
        )
        .sort(
          (left, right) =>
            right.priority - left.priority || left.id.localeCompare(right.id),
        )[0] ?? null
    );
  }
}

export const surfacePresenterRegistry = new SurfacePresenterRegistry();
