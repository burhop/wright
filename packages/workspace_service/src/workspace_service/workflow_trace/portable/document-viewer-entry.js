import { micromark } from "micromark";
import { gfm, gfmHtml } from "micromark-extension-gfm";

window.WrightDocumentViewer = {
  markdown: (text) =>
    micromark(text, {
      extensions: [gfm()],
      htmlExtensions: [gfmHtml()],
      allowDangerousHtml: false,
      allowDangerousProtocol: false,
    }),
};
