import type { DraftCanvasIntent } from "./draft-intents";
import type { DraftProjection } from "./draft-projection";

export interface DraftCanvasAdapterProps {
  readonly projection: Readonly<DraftProjection>;
  readonly selectedSemanticId: string | null;
  readonly onIntent: (intent: DraftCanvasIntent) => void;
}

export type DraftCanvasRenderer = (
  props: DraftCanvasAdapterProps,
) => ReactNode;
import type { ReactNode } from "react";
