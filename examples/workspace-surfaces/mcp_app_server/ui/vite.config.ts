import { defineConfig, type Plugin } from "vite";

function singleFile(): Plugin {
  return {
    name: "wright-reference-single-file",
    enforce: "post",
    generateBundle(_options, bundle) {
      const html = Object.values(bundle).find((item) => item.type === "asset" && item.fileName === "index.html");
      const script = Object.values(bundle).find((item) => item.type === "chunk" && item.isEntry);
      const styles = Object.values(bundle).filter((item) => item.type === "asset" && item.fileName.endsWith(".css"));
      if (!html || html.type !== "asset" || !script || script.type !== "chunk") throw new Error("Expected one HTML entry and script");
      let source = String(html.source)
        .replace(/<script[^>]+src="[^"]+"[^>]*><\/script>/, () => `<script type="module">${script.code}</script>`)
        .replace(/\s*<link rel="modulepreload"[^>]*>/g, "")
        .replace(/\s*<link rel="stylesheet"[^>]*>/g, "");
      const css = styles.map((item) => String(item.source)).join("\n");
      if (css) source = source.replace("</head>", () => `<style>${css}</style></head>`);
      source = source.replace(/^[ \t]+$/gm, "");
      html.source = source;
      for (const item of Object.values(bundle)) {
        if (item.fileName !== "index.html") delete bundle[item.fileName];
      }
    },
  };
}

export default defineConfig({ base: "./", plugins: [singleFile()], build: { cssCodeSplit: false } });
