import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import perfectionist from "eslint-plugin-perfectionist";
import simpleImportSort from "eslint-plugin-simple-import-sort";
import globals from "globals";
import tseslint from "typescript-eslint";

export default defineConfig([
  {
    extends: ["js/recommended"],
    files: ["**/*.{js,mjs,cjs,ts,mts,cts}"],
    languageOptions: {
      globals: globals.browser,
    },
    plugins: {
      js,
      perfectionist,
      "simple-import-sort": simpleImportSort,
    },
    rules: {
      // Sort TypeScript interfaces
      "perfectionist/sort-interfaces": [
        "error",
        {
          order: "asc",
          type: "natural",
        },
      ],
      // Sort TypeScript type members
      "perfectionist/sort-object-types": [
        "error",
        {
          order: "asc",
          type: "natural",
        },
      ],

      // Sort object keys
      "perfectionist/sort-objects": [
        "error",
        {
          order: "asc",
          type: "natural",
        },
      ],

      "simple-import-sort/exports": "error",

      // Sort imports and exports
      "simple-import-sort/imports": "error",
    },
  },

  tseslint.configs.recommended,
]);
