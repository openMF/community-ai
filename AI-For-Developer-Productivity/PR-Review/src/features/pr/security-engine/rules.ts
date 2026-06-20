import type { SecurityRule } from "@src/features/pr/security-engine";

export const rules: SecurityRule[] = [
  {
    description:
      "GitHub token detected. Credentials must not be committed to source control. Store the token using a secure secret management solution.",
    id: "github-token",
    pattern:
      /\b(gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{20,255})\b/,
    severity: "high",
  },
  {
    description:
      "Google API key detected. API keys must not be stored in source code. Load the key from secure configuration at runtime.",
    id: "google-api-key",
    pattern: /AIza[0-9A-Za-z\-_]{35}/,
    severity: "high",
  },
  {
    description:
      "OpenAI API key detected. API keys must not be committed to source control. Store the key using a secure secret management solution.",
    id: "openai-api-key",
    pattern: /\bsk-[A-Za-z0-9]{20,}\b/,
    severity: "high",
  },
  {
    description:
      "Anthropic API key detected. API keys must not be committed to source control. Store the key using a secure secret management solution.",
    id: "anthropic-api-key",
    pattern: /\bsk-ant-[A-Za-z0-9\-_]{20,}\b/,
    severity: "high",
  },
  {
    description:
      "AWS access key detected. Cloud credentials must not be committed to source control. Store credentials using a secure secret management solution.",
    id: "aws-access-key",
    pattern: /\bAKIA[0-9A-Z]{16}\b/,
    severity: "high",
  },
  {
    description:
      "Private key detected. Private keys must not be stored in the repository. Remove the key and rotate it if it has been exposed.",
    id: "private-key",
    pattern: /-----BEGIN (RSA|EC|OPENSSH|PGP|DSA) PRIVATE KEY-----/,
    severity: "high",
  },
  {
    description:
      "Hardcoded credential detected. Secrets must not be stored in source code. Load credentials from secure configuration at runtime.",
    fileExtensions: [
      ".java",
      ".kt",
      ".js",
      ".jsx",
      ".ts",
      ".tsx",
      ".py",
      ".dart",
      ".xml",
      ".yml",
      ".yaml",
      ".properties",
      ".env",
    ],
    id: "hardcoded-secret",
    pattern:
      /\b(secret|password|token|apikey|api_key|auth_token|access_token|secret_key)\b\s*[:=]\s*['"`]([^'"`\n]{8,})['"`]/i,
    severity: "high",
  },
  {
    description:
      "Use of eval() detected. Dynamic code execution can introduce security vulnerabilities. Consider using a safer alternative.",
    fileExtensions: [".js", ".jsx", ".ts", ".tsx"],
    id: "eval-usage",
    pattern: /\beval\s*\(/,
    severity: "medium",
  },
];
