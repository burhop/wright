import { defineConfig, type Plugin } from "vite";

function replaceTag(
  source: string,
  marker: string,
  replacement: string,
  closingTag = "",
): string {
  const start = source.indexOf(marker);
  if (start < 0) return source;
  const endMarker = closingTag || ">";
  const end = source.indexOf(endMarker, start);
  if (end < 0) throw new Error(`Unterminated ${marker} tag in Vite output`);
  return (
    source.slice(0, start) + replacement + source.slice(end + endMarker.length)
  );
}

function removeAllTags(source: string, marker: string): string {
  let result = source;
  while (result.includes(marker)) result = replaceTag(result, marker, "");
  return result;
}

function singleFile(): Plugin {
  return {
    name: "wright-reference-single-file",
    enforce: "post",
    generateBundle(_options, bundle) {
      const html = Object.values(bundle).find(
        (item) => item.type === "asset" && item.fileName === "index.html",
      );
      const script = Object.values(bundle).find(
        (item) => item.type === "chunk" && item.isEntry,
      );
      const styles = Object.values(bundle).filter(
        (item) => item.type === "asset" && item.fileName.endsWith(".css"),
      );
      if (!html || html.type !== "asset" || !script || script.type !== "chunk")
        throw new Error("Expected one HTML entry and script");
      let source = replaceTag(
        String(html.source),
        '<script type="module"',
        `<script type="module">${script.code}</script>`,
        "</script>",
      );
      source = removeAllTags(source, '<link rel="modulepreload"');
      source = removeAllTags(source, '<link rel="stylesheet"');
      const css = styles.map((item) => String(item.source)).join("\n");
      if (css)
        source = source.replace(
          "</head>",
          () => `<style>${css}</style></head>`,
        );
      source = source.replace(/^[ \t]+$/gm, "");
      html.source = source;
      for (const item of Object.values(bundle)) {
        if (item.fileName !== "index.html") delete bundle[item.fileName];
      }
    },
  };
}

export default defineConfig({
  base: "./",
  plugins: [singleFile()],
  build: { cssCodeSplit: false },
});
