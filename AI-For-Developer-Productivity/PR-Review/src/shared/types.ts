import type { SecurityRule } from "@src/features/pr/security-engine";

export interface Config {
  dependencyFiles?: string[];
  filesToScan?: string[];
  ignore?: string[];
  model?: string;
  rules?: SecurityRule[];
}
