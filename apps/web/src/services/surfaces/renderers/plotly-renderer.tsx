import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

export interface PlotlyModule {
  react(
    host: HTMLElement,
    data: readonly unknown[],
    layout?: Readonly<Record<string, unknown>>,
    config?: Readonly<Record<string, unknown>>,
  ): Promise<unknown> | unknown;
  purge(host: HTMLElement): void;
}

interface PlotlyRepresentation {
  readonly mediaType: "application/vnd.plotly.v1+json";
  readonly encoding: "json";
  readonly data: unknown;
}

interface Props {
  readonly representation: PlotlyRepresentation;
  readonly description: string;
  readonly fallback: ReactNode;
  readonly loadPlotly?: () => Promise<PlotlyModule>;
}

interface PlotValue {
  data: readonly unknown[];
  layout: Readonly<Record<string, unknown>>;
}

function finiteJson(value: unknown, depth = 0): boolean {
  if (depth > 32) return false;
  if (typeof value === "number") return Number.isFinite(value);
  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "boolean"
  ) {
    return true;
  }
  if (Array.isArray(value)) return value.every((item) => finiteJson(item, depth + 1));
  if (typeof value === "object") {
    return Object.values(value).every((item) => finiteJson(item, depth + 1));
  }
  return false;
}

function parsePlot(value: unknown): PlotValue | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }
  const plot = value as Record<string, unknown>;
  if (!Array.isArray(plot.data) || !finiteJson(plot)) return null;
  if (
    plot.layout !== undefined &&
    (typeof plot.layout !== "object" ||
      plot.layout === null ||
      Array.isArray(plot.layout))
  ) {
    return null;
  }
  return {
    data: plot.data,
    layout: (plot.layout ?? {}) as Readonly<Record<string, unknown>>,
  };
}

async function loadBundledPlotly(): Promise<PlotlyModule> {
  const module = await import("plotly.js-dist-min");
  return (module.default ?? module) as unknown as PlotlyModule;
}

export function PlotlyRenderer({
  representation,
  description,
  fallback,
  loadPlotly = loadBundledPlotly,
}: Props) {
  const host = useRef<HTMLDivElement>(null);
  const module = useRef<PlotlyModule | null>(null);
  const loading = useRef<Promise<PlotlyModule> | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error" | "invalid">(
    "loading",
  );
  const plot = useMemo(() => parsePlot(representation.data), [representation.data]);

  useEffect(() => {
    if (!plot) {
      setStatus("invalid");
      return;
    }
    let cancelled = false;
    const renderPlot = async () => {
      try {
        loading.current ??= module.current
          ? Promise.resolve(module.current)
          : loadPlotly();
        const plotly = await loading.current;
        module.current = plotly;
        if (cancelled || !host.current) return;
        await plotly.react(host.current, plot.data, plot.layout, {
          responsive: true,
          displaylogo: false,
        });
        if (!cancelled) setStatus("ready");
      } catch {
        if (!cancelled) setStatus("error");
      }
    };
    void renderPlot();
    return () => {
      cancelled = true;
    };
  }, [loadPlotly, plot]);

  useEffect(
    () => () => {
      if (host.current && module.current) module.current.purge(host.current);
    },
    [],
  );

  return (
    <div>
      {status === "invalid" && <div role="alert">Invalid Plotly display data.</div>}
      {status === "error" && (
        <div role="alert">The interactive graph could not render.</div>
      )}
      {status !== "ready" && fallback}
      <div
        ref={host}
        role="img"
        aria-label={description}
        hidden={status !== "ready"}
        style={{ width: "100%", minHeight: 320 }}
      />
    </div>
  );
}
