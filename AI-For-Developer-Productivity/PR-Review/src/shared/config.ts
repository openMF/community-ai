import * as fs from "node:fs";
import * as path from "node:path";

import type { Config } from "@src/shared";
import yaml from "yaml";

let cachedConfig: Config | null = null;

export function loadConfig(workspacePath: string | undefined): Config {
  if (!workspacePath) {
    console.warn("No workspace path provided, using default configuration.");
    cachedConfig = {};
    return cachedConfig;
  }
  if (cachedConfig) {
    return cachedConfig;
  }

  const configPath = path.join(workspacePath, "prowl.yml");
  if (!fs.existsSync(configPath)) {
    cachedConfig = {};
    return cachedConfig;
  }

  try {
    const fileContent = fs.readFileSync(configPath, "utf-8");
    const parsed = yaml.parse(fileContent);
    cachedConfig = (parsed as Config) || {};
    return cachedConfig;
  } catch (err) {
    console.error("Failed to parse prowl.yml:", err);
    cachedConfig = {};
    return cachedConfig;
  }
}

export function getConfig(): Config {
  if (!cachedConfig) {
    const workspace = process.env["GITHUB_WORKSPACE"];
    return loadConfig(workspace);
  }
  return cachedConfig;
}
