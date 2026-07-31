import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  type Dispatch,
  type ReactNode,
} from "react";
import {
  parseSurfaceDescriptor,
  type SurfaceDescriptor,
} from "../services/surfaces/surface-contract";
import type { SurfacePresenter } from "../services/surfaces/registry";

export const SURFACE_STATE_VERSION = 2 as const;

export interface SurfaceLayout {
  readonly mode: "normal" | "focus";
  readonly chatSize: {
    readonly unit: "ratio" | "pixels";
    readonly value: number;
  };
}

export interface SurfaceState {
  readonly version: 2;
  readonly byId: Readonly<Record<string, SurfaceDescriptor>>;
  readonly tabs: readonly string[];
  readonly activeSurfaceId: string | null;
  readonly layout: SurfaceLayout;
}

export type SurfaceAction =
  | { readonly type: "upsert"; readonly descriptor: SurfaceDescriptor }
  | { readonly type: "activate"; readonly surfaceId: string | null }
  | { readonly type: "remove"; readonly surfaceId: string }
  | { readonly type: "layout"; readonly layout: SurfaceLayout };

const defaultLayout: SurfaceLayout = {
  mode: "normal",
  chatSize: { unit: "ratio", value: 0.4 },
};

export function createSurfaceState(): SurfaceState {
  return {
    version: SURFACE_STATE_VERSION,
    byId: {},
    tabs: [],
    activeSurfaceId: null,
    layout: defaultLayout,
  };
}

export function reduceSurfaceState(
  state: SurfaceState,
  action: SurfaceAction,
): SurfaceState {
  switch (action.type) {
    case "upsert": {
      const current = state.byId[action.descriptor.surfaceId];
      if (current && current.revision >= action.descriptor.revision) {
        return state;
      }
      const exists = Boolean(current);
      return {
        ...state,
        byId: {
          ...state.byId,
          [action.descriptor.surfaceId]: action.descriptor,
        },
        tabs: exists
          ? state.tabs
          : [...state.tabs, action.descriptor.surfaceId],
        activeSurfaceId: state.activeSurfaceId ?? action.descriptor.surfaceId,
      };
    }
    case "activate":
      if (action.surfaceId !== null && !state.byId[action.surfaceId]) {
        return state;
      }
      return { ...state, activeSurfaceId: action.surfaceId };
    case "remove": {
      if (!state.byId[action.surfaceId]) return state;
      const byId = { ...state.byId };
      delete byId[action.surfaceId];
      const tabs = state.tabs.filter((item) => item !== action.surfaceId);
      return {
        ...state,
        byId,
        tabs,
        activeSurfaceId:
          state.activeSurfaceId === action.surfaceId
            ? (tabs.at(-1) ?? null)
            : state.activeSurfaceId,
      };
    }
    case "layout":
      return { ...state, layout: validateLayout(action.layout) };
  }
}

function validateLayout(value: SurfaceLayout): SurfaceLayout {
  if (!(["normal", "focus"] as const).includes(value.mode)) {
    throw new TypeError("surface layout mode is invalid");
  }
  if (!(["ratio", "pixels"] as const).includes(value.chatSize.unit)) {
    throw new TypeError("surface chat size unit is invalid");
  }
  if (!Number.isFinite(value.chatSize.value) || value.chatSize.value <= 0) {
    throw new TypeError("surface chat size must be positive");
  }
  if (value.chatSize.unit === "ratio" && value.chatSize.value >= 1) {
    throw new TypeError("surface chat ratio must be below one");
  }
  return {
    mode: value.mode,
    chatSize: { unit: value.chatSize.unit, value: value.chatSize.value },
  };
}

export function serializeSurfaceState(state: SurfaceState): string {
  return JSON.stringify({
    version: SURFACE_STATE_VERSION,
    descriptors: state.tabs.map((surfaceId) => state.byId[surfaceId]),
    tabs: state.tabs,
    activeSurfaceId: state.activeSurfaceId,
    layout: state.layout,
  });
}

export function restoreSurfaceState(serialized: string): SurfaceState {
  const value = JSON.parse(serialized) as Record<string, unknown>;
  if (value.version === 1) {
    const surfaces = Array.isArray(value.surfaces) ? value.surfaces : [];
    const focus = Boolean(
      (value.layout as Record<string, unknown> | undefined)?.focus,
    );
    const chatWidth = Number(
      (value.layout as Record<string, unknown> | undefined)?.chatWidth,
    );
    return restoreVersionTwo({
      version: 2,
      descriptors: surfaces,
      tabs: surfaces.map((item) =>
        String((item as Record<string, unknown>).surfaceId),
      ),
      activeSurfaceId: value.activeSurfaceId,
      layout: {
        mode: focus ? "focus" : "normal",
        chatSize: {
          unit: "pixels",
          value: Number.isFinite(chatWidth) && chatWidth > 0 ? chatWidth : 420,
        },
      },
    });
  }
  if (value.version !== SURFACE_STATE_VERSION) {
    throw new TypeError("unsupported surface state version");
  }
  return restoreVersionTwo(value);
}

function restoreVersionTwo(value: Record<string, unknown>): SurfaceState {
  if (!Array.isArray(value.descriptors) || !Array.isArray(value.tabs)) {
    throw new TypeError("surface state descriptors and tabs are required");
  }
  const descriptors = value.descriptors.map(parseSurfaceDescriptor);
  const byId = Object.fromEntries(
    descriptors.map((descriptor) => [descriptor.surfaceId, descriptor]),
  );
  const tabs = value.tabs.map((item) => String(item));
  if (
    new Set(tabs).size !== tabs.length ||
    tabs.some((surfaceId) => !byId[surfaceId])
  ) {
    throw new TypeError("surface state tabs are malformed");
  }
  const activeSurfaceId =
    value.activeSurfaceId === null || value.activeSurfaceId === undefined
      ? null
      : String(value.activeSurfaceId);
  if (activeSurfaceId !== null && !byId[activeSurfaceId]) {
    throw new TypeError("active surface is not present in tabs");
  }
  return {
    version: 2,
    byId,
    tabs,
    activeSurfaceId,
    layout: validateLayout(value.layout as SurfaceLayout),
  };
}

export class SurfacePresenterDeck {
  private readonly presenters = new Map<string, SurfacePresenter>();
  private readonly disposed = new WeakSet<SurfacePresenter>();

  set(surfaceId: string, presenter: SurfacePresenter): void {
    const existing = this.presenters.get(surfaceId);
    if (existing && existing !== presenter) this.disposePresenter(existing);
    this.presenters.set(surfaceId, presenter);
  }

  get(surfaceId: string): SurfacePresenter | undefined {
    return this.presenters.get(surfaceId);
  }

  remove(surfaceId: string): void {
    const presenter = this.presenters.get(surfaceId);
    if (!presenter) return;
    this.presenters.delete(surfaceId);
    this.disposePresenter(presenter);
  }

  dispose(): void {
    for (const presenter of this.presenters.values()) {
      this.disposePresenter(presenter);
    }
    this.presenters.clear();
  }

  private disposePresenter(presenter: SurfacePresenter): void {
    if (this.disposed.has(presenter)) return;
    this.disposed.add(presenter);
    presenter.dispose();
  }
}

interface SurfaceStateContextValue {
  readonly state: SurfaceState;
  readonly dispatch: Dispatch<SurfaceAction>;
  readonly deck: SurfacePresenterDeck;
}

const SurfaceStateContext = createContext<SurfaceStateContextValue | null>(
  null,
);

export function SurfaceStateProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reduceSurfaceState, undefined, () =>
    createSurfaceState(),
  );
  const deck = useMemo(() => new SurfacePresenterDeck(), []);
  useEffect(() => () => deck.dispose(), [deck]);
  return (
    <SurfaceStateContext.Provider value={{ state, dispatch, deck }}>
      {children}
    </SurfaceStateContext.Provider>
  );
}

export function useSurfaces(): SurfaceStateContextValue {
  const context = useContext(SurfaceStateContext);
  if (!context) {
    throw new Error("useSurfaces must be used inside SurfaceStateProvider");
  }
  return context;
}
