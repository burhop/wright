import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import license from "rollup-plugin-license";
import path from "path";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    license({
      thirdParty: {
        output: {
          file: path.resolve(__dirname, "dist/third-party-licenses-web.txt"),
          encoding: "utf-8",
        },
      },
    }),
  ],
  server: {
    allowedHosts: ["promaxgb10-9666"],
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
  },
});
