import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";
import { defineConfig, globalIgnores } from "eslint/config";

export default defineConfig([
  globalIgnores(["dist"]),
  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
    },
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-unused-vars": "off",
      "no-case-declarations": "off",
      "no-empty": "off",
      "no-useless-catch": "off",
      "no-useless-assignment": "off",
      "react-refresh/only-export-components": "off",
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/purity": "off",
      "no-useless-escape": "off",
      "react-hooks/immutability": "off",
    },
  },
]);
