/** Presentation choices only. These values confer no session or API authority. */
export interface PresentationProfile {
  readonly mode: "wright" | "embedded-browser";
  readonly chat: "wright" | "host";
  readonly documents: "wright" | "single-panel";
  readonly controlStyle: "wright" | "neutral";
}

const wright: PresentationProfile = Object.freeze({
  mode: "wright",
  chat: "wright",
  documents: "wright",
  controlStyle: "wright",
});
const embeddedBrowser: PresentationProfile = Object.freeze({
  mode: "embedded-browser",
  chat: "host",
  documents: "wright",
  controlStyle: "neutral",
});

/** A URL hint affects composition; native panel/tab support requires a host handshake. */
export function presentationForSearch(search: string): PresentationProfile {
  return new URLSearchParams(search).get("host") === "openai-desktop"
    ? embeddedBrowser
    : wright;
}
