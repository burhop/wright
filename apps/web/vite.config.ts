import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import license from "rollup-plugin-license";
import path from "path";

// https://vite.dev/config/
export default defineConfig(({ command }) => {
  const isBuild = command === "build";
  const isDesktop = process.env.BUILD_TARGET === "desktop";
  
  return {
    base: isDesktop ? "./" : "/",
    plugins: [
      react(),
      license({
        thirdParty: {
          output: {
            file: isBuild
              ? path.resolve(__dirname, isDesktop ? "dist-desktop/third-party-licenses-web.txt" : "dist/third-party-licenses-web.txt")
              : path.resolve(__dirname, "public/third-party-licenses-web.txt"),
            encoding: "utf-8",
          },
        },
      }),
    ],
    build: {
      outDir: isDesktop ? "dist-desktop" : "dist",
    },
    server: {
      allowedHosts: ["promaxgb10-9666"],
    },
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: "./src/test/setup.ts",
    },
  };
});
