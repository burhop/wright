export const WORKSPACE_LAYOUT_VERSION = 2 as const;
export const BASIS_POINTS = 10_000;
export const CHAT_MINIMUM_PX = 320;
export const SURFACE_MINIMUM_PX = 480;
export const SEPARATOR_SIZE_PX = 8;
export const NARROW_BREAKPOINT_PX =
  CHAT_MINIMUM_PX + SURFACE_MINIMUM_PX + SEPARATOR_SIZE_PX;
export const NORMAL_CHAT_DEFAULT_BP = 3_800;
export const FOCUS_CHAT_DEFAULT_PX = 360;
export const FOCUS_CHAT_MAXIMUM_PX = 720;
export const FOCUS_CHAT_MAXIMUM_BP = 5_000;

export type WideWorkspaceMode = "normal" | "focus";
export type WorkspaceLayoutMode = WideWorkspaceMode | "narrow";
export type NarrowPane = "chat" | "surface";

export interface WorkspaceLayoutState {
  readonly version: 2;
  readonly mode: WorkspaceLayoutMode;
  readonly wideMode: WideWorkspaceMode;
  readonly normalChatBasisPoints: number;
  readonly focusChatBasisPoints: number;
  readonly focusChatCustomized: boolean;
  readonly narrowPane: NarrowPane;
}

export interface ResolvedWorkspaceLayout {
  readonly mode: WorkspaceLayoutMode;
  readonly chatBasisPoints: number;
  readonly minimumChatBasisPoints: number;
  readonly maximumChatBasisPoints: number;
  readonly chatPixels: number;
  readonly surfacePixels: number;
  readonly separatorPixels: number;
}

export type WorkspaceLayoutAction =
  | { readonly type: "resize_container"; readonly containerWidth: number }
  | { readonly type: "enter_focus"; readonly containerWidth: number }
  | { readonly type: "exit_focus"; readonly containerWidth: number }
  | {
      readonly type: "set_chat_basis_points";
      readonly value: number;
      readonly containerWidth: number;
    }
  | { readonly type: "select_narrow_pane"; readonly pane: NarrowPane };

function usableWidth(containerWidth: number): number {
  return Math.max(1, Math.floor(containerWidth) - SEPARATOR_SIZE_PX);
}

function toBasisPoints(pixels: number, width: number): number {
  return Math.round((pixels / usableWidth(width)) * BASIS_POINTS);
}

function toPixels(basisPoints: number, width: number): number {
  return Math.round((usableWidth(width) * basisPoints) / BASIS_POINTS);
}

function wideBounds(containerWidth: number): {
  readonly minimum: number;
  readonly maximum: number;
} {
  const width = usableWidth(containerWidth);
  return {
    minimum: Math.ceil((CHAT_MINIMUM_PX / width) * BASIS_POINTS),
    maximum: Math.floor(((width - SURFACE_MINIMUM_PX) / width) * BASIS_POINTS),
  };
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, Math.round(value)));
}

function focusDefaultBasisPoints(containerWidth: number): number {
  const { minimum, maximum } = wideBounds(containerWidth);
  const pixelMaximum = toBasisPoints(FOCUS_CHAT_MAXIMUM_PX, containerWidth);
  return clamp(
    toBasisPoints(FOCUS_CHAT_DEFAULT_PX, containerWidth),
    minimum,
    Math.min(maximum, FOCUS_CHAT_MAXIMUM_BP, pixelMaximum),
  );
}

function actualMode(
  wideMode: WideWorkspaceMode,
  containerWidth: number,
): WorkspaceLayoutMode {
  return containerWidth < NARROW_BREAKPOINT_PX ? "narrow" : wideMode;
}

export function createWorkspaceLayout(
  containerWidth: number,
): WorkspaceLayoutState {
  const safeWidth = Math.max(1, containerWidth);
  return {
    version: WORKSPACE_LAYOUT_VERSION,
    mode: actualMode("normal", safeWidth),
    wideMode: "normal",
    normalChatBasisPoints: NORMAL_CHAT_DEFAULT_BP,
    focusChatBasisPoints:
      safeWidth >= NARROW_BREAKPOINT_PX
        ? focusDefaultBasisPoints(safeWidth)
        : NORMAL_CHAT_DEFAULT_BP,
    focusChatCustomized: false,
    narrowPane: "chat",
  };
}

export function resolveWorkspaceLayout(
  state: WorkspaceLayoutState,
  containerWidth: number,
): ResolvedWorkspaceLayout {
  const width = Math.max(1, Math.floor(containerWidth));
  if (state.mode === "narrow" || width < NARROW_BREAKPOINT_PX) {
    return {
      mode: "narrow",
      chatBasisPoints:
        state.wideMode === "focus"
          ? state.focusChatBasisPoints
          : state.normalChatBasisPoints,
      minimumChatBasisPoints: 0,
      maximumChatBasisPoints: BASIS_POINTS,
      chatPixels: width,
      surfacePixels: width,
      separatorPixels: 0,
    };
  }

  const bounds = wideBounds(width);
  const selected =
    state.wideMode === "focus"
      ? state.focusChatBasisPoints
      : state.normalChatBasisPoints;
  const maximum =
    state.wideMode === "focus"
      ? Math.min(
          bounds.maximum,
          FOCUS_CHAT_MAXIMUM_BP,
          toBasisPoints(FOCUS_CHAT_MAXIMUM_PX, width),
        )
      : bounds.maximum;
  const chatBasisPoints = clamp(selected, bounds.minimum, maximum);
  const chatPixels = toPixels(chatBasisPoints, width);
  return {
    mode: state.wideMode,
    chatBasisPoints,
    minimumChatBasisPoints: bounds.minimum,
    maximumChatBasisPoints: maximum,
    chatPixels,
    surfacePixels: usableWidth(width) - chatPixels,
    separatorPixels: SEPARATOR_SIZE_PX,
  };
}

export function workspaceLayoutReducer(
  state: WorkspaceLayoutState,
  action: WorkspaceLayoutAction,
): WorkspaceLayoutState {
  switch (action.type) {
    case "resize_container":
      return {
        ...state,
        mode: actualMode(state.wideMode, action.containerWidth),
      };
    case "enter_focus":
      return {
        ...state,
        wideMode: "focus",
        mode: actualMode("focus", action.containerWidth),
        focusChatBasisPoints: state.focusChatCustomized
          ? state.focusChatBasisPoints
          : focusDefaultBasisPoints(
              Math.max(NARROW_BREAKPOINT_PX, action.containerWidth),
            ),
      };
    case "exit_focus":
      return {
        ...state,
        wideMode: "normal",
        mode: actualMode("normal", action.containerWidth),
      };
    case "select_narrow_pane":
      return { ...state, narrowPane: action.pane };
    case "set_chat_basis_points": {
      if (action.containerWidth < NARROW_BREAKPOINT_PX) return state;
      const resolved = resolveWorkspaceLayout(state, action.containerWidth);
      const value = clamp(
        action.value,
        resolved.minimumChatBasisPoints,
        resolved.maximumChatBasisPoints,
      );
      return state.wideMode === "focus"
        ? { ...state, focusChatBasisPoints: value, focusChatCustomized: true }
        : { ...state, normalChatBasisPoints: value };
    }
  }
}

function isBasisPoints(value: unknown): value is number {
  return (
    Number.isInteger(value) &&
    (value as number) > 0 &&
    (value as number) < BASIS_POINTS
  );
}

export function restoreWorkspaceLayout(
  serialized: string | null,
  containerWidth: number,
): WorkspaceLayoutState {
  const fallback = createWorkspaceLayout(containerWidth);
  if (!serialized) return fallback;
  try {
    const value = JSON.parse(serialized) as Record<string, unknown>;
    if (value.version === 1) {
      const chatWidth = Number(value.chatWidth);
      const wideMode: WideWorkspaceMode =
        value.focus === true ? "focus" : "normal";
      const migratedBasisPoints =
        Number.isFinite(chatWidth) && chatWidth > 0
          ? toBasisPoints(
              chatWidth,
              Math.max(containerWidth, NARROW_BREAKPOINT_PX),
            )
          : wideMode === "focus"
            ? fallback.focusChatBasisPoints
            : fallback.normalChatBasisPoints;
      return {
        ...fallback,
        wideMode,
        mode: actualMode(wideMode, containerWidth),
        ...(wideMode === "focus"
          ? {
              focusChatBasisPoints: migratedBasisPoints,
              focusChatCustomized: true,
            }
          : { normalChatBasisPoints: migratedBasisPoints }),
      };
    }
    if (
      value.version !== WORKSPACE_LAYOUT_VERSION ||
      (value.wideMode !== "normal" && value.wideMode !== "focus") ||
      !isBasisPoints(value.normalChatBasisPoints) ||
      !isBasisPoints(value.focusChatBasisPoints) ||
      (value.narrowPane !== "chat" && value.narrowPane !== "surface")
    ) {
      return fallback;
    }
    const wideMode = value.wideMode;
    return {
      version: WORKSPACE_LAYOUT_VERSION,
      wideMode,
      mode: actualMode(wideMode, containerWidth),
      normalChatBasisPoints: value.normalChatBasisPoints,
      focusChatBasisPoints: value.focusChatBasisPoints,
      focusChatCustomized: value.focusChatCustomized === true,
      narrowPane: value.narrowPane,
    };
  } catch {
    return fallback;
  }
}

export function serializeWorkspaceLayout(state: WorkspaceLayoutState): string {
  return JSON.stringify({
    version: state.version,
    wideMode: state.wideMode,
    normalChatBasisPoints: state.normalChatBasisPoints,
    focusChatBasisPoints: state.focusChatBasisPoints,
    focusChatCustomized: state.focusChatCustomized,
    narrowPane: state.narrowPane,
  });
}
