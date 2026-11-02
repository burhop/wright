// Passive views of allowlisted report bytes. No workspace or execution client.
import { createElement } from "react";
import { createRoot } from "react-dom/client";
import { MarkdownDocument } from "../../../packages/ui_kit/src/documents";
import { ThreeDViewer } from "../../../packages/ui_kit/src/geometry";

export function documentView(host: HTMLElement, text: string) {
  const root = createRoot(host);
  root.render(createElement(MarkdownDocument, { text }));
  return () => root.unmount();
}

export function modelView(host: HTMLElement, arrayBuffer: ArrayBuffer, fileName: string) {
  const root = createRoot(host);
  root.render(createElement(ThreeDViewer, { arrayBuffer, fileName }));
  return () => root.unmount();
}
