import type { McpUiHostContext } from "@modelcontextprotocol/ext-apps";
import type { NativeNavigationState } from "./native-navigation-state";

export interface ReviewLocation {
  navigation?: NativeNavigationState;
  active_surface: "home" | "workflow";
  editor_has_unsaved_changes: boolean;
}
export interface ReviewEvent {
  elapsed_ms: number;
  kind:
    "navigation" | "host-context" | "resize" | "error" | "unhandled-rejection";
  location?: ReviewLocation;
}
const round = (value: number) => Math.round(value * 10) / 10;
const box = (value: DOMRect) => ({
  x: round(value.x),
  y: round(value.y),
  width: round(value.width),
  height: round(value.height),
});
const styles = [
  "--color-background-primary",
  "--color-text-primary",
  "--color-text-secondary",
  "--color-border-primary",
  "--font-sans",
] as const;
function safeStyle(value: unknown) {
  return typeof value === "string" &&
    value.length < 160 &&
    !/[;{}@<>]|url\s*\(/i.test(value)
    ? value
    : undefined;
}
function elementGeometry(element: Element) {
  const rect = element.getBoundingClientRect();
  const css = getComputedStyle(element);
  const testId = element.getAttribute("data-testid") ?? "";
  return {
    tag: element.tagName.toLowerCase(),
    ...(/^[a-z][a-z0-9-]{0,95}$/.test(testId) ? { test_id: testId } : {}),
    rect: box(rect),
    font: {
      family: safeStyle(css.fontFamily),
      size: css.fontSize,
      line_height: css.lineHeight,
    },
    color: safeStyle(css.color),
    background: safeStyle(css.backgroundColor),
    in_viewport:
      rect.right > 0 &&
      rect.bottom > 0 &&
      rect.left < innerWidth &&
      rect.top < innerHeight,
    horizontal_clip: rect.left < -1 || rect.right > innerWidth + 1,
  };
}

/** Explicit, bounded observations from our iframe only. No DOM text or input values. */
export function captureUiReview(
  root: HTMLElement,
  host: McpUiHostContext | undefined,
  location: ReviewLocation,
  events: readonly ReviewEvent[],
  target?: Element,
) {
  const variables = Object.fromEntries(
    styles.flatMap((key) => {
      const value = safeStyle(host?.styles?.variables?.[key]);
      return value === undefined ? [] : [[key, value]];
    }),
  );
  const dimensions = Object.fromEntries(
    ["width", "height", "maxWidth", "maxHeight"].flatMap((key) => {
      const value = (
        host?.containerDimensions as Record<string, unknown> | undefined
      )?.[key];
      return typeof value === "number" && Number.isFinite(value) && value >= 0
        ? [[key, round(Math.min(value, 100_000))]]
        : [];
    }),
  );
  const tool = host?.toolInfo?.tool._meta?.ui as
    { resourceUri?: unknown } | undefined;
  const uri = tool?.resourceUri;
  const build = (
    globalThis as unknown as {
      __WRIGHT_NATIVE_BUILD__?: { bundle_payload_sha256?: string };
    }
  ).__WRIGHT_NATIVE_BUILD__;
  const all = Array.from(
    root.querySelectorAll("button,input,select,textarea,[role=tab],h1,h2"),
  ).filter((element) => {
    const css = getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    return (
      css.display !== "none" &&
      css.visibility !== "hidden" &&
      rect.width > 0 &&
      rect.height > 0
    );
  });
  const targetPath: string[] = [];
  for (
    let node = target;
    node && node !== root && root.contains(node) && targetPath.length < 10;
    node = node.parentElement ?? undefined
  ) {
    const siblings = Array.from(node.parentElement?.children ?? []).filter(
      (other) => other.tagName === node!.tagName,
    );
    targetPath.unshift(
      `${node.tagName.toLowerCase()}:nth-of-type(${siblings.indexOf(node) + 1})`,
    );
  }
  return {
    schema_version: "wright.ui-review/1",
    captured_at: new Date().toISOString(),
    evidence_boundary:
      "Wright iframe measurements; host claims are reported signals, not native screenshots or user acceptance",
    build: {
      bundle_payload_sha256: build?.bundle_payload_sha256 ?? null,
      resource_uri:
        typeof uri === "string" &&
        /^ui:\/\/wright\/workflow\/[a-f0-9]{64}\.html$/.test(uri)
          ? uri
          : null,
    },
    location: structuredClone(location),
    host: {
      available: host !== undefined,
      theme: ["light", "dark"].includes(String(host?.theme))
        ? host?.theme
        : null,
      display_mode: ["inline", "fullscreen", "pip"].includes(
        String(host?.displayMode),
      )
        ? host?.displayMode
        : null,
      platform: ["web", "desktop", "mobile"].includes(String(host?.platform))
        ? host?.platform
        : null,
      container_dimensions: dimensions,
      style_variables: variables,
    },
    viewport: {
      width: innerWidth,
      height: innerHeight,
      device_pixel_ratio: devicePixelRatio,
    },
    root: {
      ...elementGeometry(root),
      scroll_width: root.scrollWidth,
      client_width: root.clientWidth,
      scroll_height: root.scrollHeight,
      client_height: root.clientHeight,
    },
    controls: all.slice(0, 80).map(elementGeometry),
    controls_truncated: all.length > 80,
    selected_element:
      target && root.contains(target)
        ? {
            ...elementGeometry(target),
            relative_selector: targetPath.join(" > "),
            control_index: all.indexOf(target),
          }
        : null,
    recent_events: structuredClone(events.slice(-20)),
    limits: [
      "No screenshot or host-shell access",
      "No form values, DOM text, source bodies, raw errors or credentials",
      "Offscreen controls may be intentional scrolling; flags require diagnosis",
    ],
  };
}
export type UiReview = ReturnType<typeof captureUiReview>;

export function uiReviewFile(report: UiReview, comment: string) {
  // Comments are deliberate user input, not ambient collection. Mask common accidental secrets.
  const safeComment = comment
    .slice(0, 500)
    .replace(/\bBearer\s+\S+/gi, "Bearer [redacted]")
    .replace(/\bsk-[a-zA-Z0-9_-]+/g, "[redacted]");
  const bytes = JSON.stringify({ ...report, comment: safeComment }, null, 2);
  if (new TextEncoder().encode(bytes).length > 64 * 1024)
    throw Error("UI report exceeds the bounded text preview size.");
  return new File([bytes], `wright-ui-review-${crypto.randomUUID()}.json`, {
    type: "application/json",
  });
}
