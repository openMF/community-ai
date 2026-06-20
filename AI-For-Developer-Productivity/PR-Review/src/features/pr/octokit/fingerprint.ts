// Generate stable identifiers for findings so they can be tracked
// across PR updates without relying on LLM-generated text.

// Normalise code snippets before using them in fingerprints.
export function normaliseSnippet(snippet: string, maxLength = 120): string {
  return snippet.trim().replace(/\s+/g, " ").toLowerCase().slice(0, maxLength);
}

// Static finding fingerprint.
// Example: static:hardcoded-secret:src/auth.ts:const api_key = "..."
export function fingerprintStatic(
  ruleId: string,
  file: string,
  lineContent: string
): string {
  return `static:${ruleId}:${file}:${normaliseSnippet(lineContent)}`;
}

// Dependency vulnerability fingerprint.
// Example: osv:lodash@4.17.20:CVE-2021-23337,GHSA-35jh-r3h4-6jhm
export function fingerprintOSV(
  pkgName: string,
  pkgVersion: string,
  osvIds: string[]
): string {
  const ids = [...osvIds].sort().join(",");

  return `osv:${pkgName}@${pkgVersion}:${ids}`;
}

// LLM finding fingerprint based on the flagged code.
// Example: llm:src/auth.ts:db.query(`select * from users`)
export function fingerprintLLM(file: string, lineContent: string): string {
  return `llm:${file}:${normaliseSnippet(lineContent)}`;
}
