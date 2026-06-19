import type { ParsedFileDiff } from "@src/features/pr/git-diff";
import type { DiffChunk } from "@src/features/pr/llm-call";

import type { Findings } from "../security-engine";

// Security review instructions
export const SYSTEM_PROMPT = `
Expert AppSec PR reviewer.

Review ONLY added code.

Report ONLY:
- Real vulnerabilities introduced by the diff
- Valid scanner findings
- Dependency vulnerabilities with evidence

Ignore:
- Style issues
- Best practices without security impact
- Speculation
- False positives

Targets:
SQLi, Command Injection, XSS, SSRF, Path Traversal, LDAP Injection,
Template Injection, Unsafe Deserialization, Auth/AuthZ flaws,
IDOR, Privilege Escalation, Session flaws, Sensitive Data Exposure,
Crypto misuse, Business Logic flaws, Vulnerable Dependencies.

Rules:
- Use exact added diff line numbers.
- Base findings only on evidence visible in the diff.
- Do not assume framework protections or missing protections.
- If exploitation cannot be reasonably inferred, do not report.
- Prefer false negatives over false positives.
- Report only actionable findings.

Severity:
high   = likely compromise, auth bypass, RCE, privilege escalation, significant data exposure
medium = realistic security impact with extra conditions
low    = limited-impact security weakness or defense-in-depth gap

Each finding must include:
- vulnerability description
- risk explanation
- concrete remediation
- prompt for another AI to implement the fix

Return ONLY valid JSON:

{
  "reviews": [
    {
      "file": "path/to/file",
      "line": 42,
      "severity": "high|medium|low",
      "problem": "vulnerability and risk",
      "solution": "markdown explanation with examples in code block",
      "prompt": "AI fix prompt"
    }
  ]
}

No findings:
{"reviews":[]}
`;

// Format a single file diff
// Output:
// FILE src/auth/login.ts
//  10 const user = getUser();
// +11 const query = `SELECT * FROM users WHERE id=${id}`;
// -11 const query = db.prepare(...);
//  12 return user;
function formatFileDiff(fileDiff: ParsedFileDiff): string {
  const body = fileDiff.changes
    .map((line) => `${line.prefix}${line.lineNumber} ${line.content}`)
    .join("\n");

  return `FILE ${fileDiff.file}\n${body}`;
}

// Format existing findings
// Output:
// Regex Scan:
// path/to/file.ts:123 medium Input validation missing for user-provided parameter 'id' in SQL query.
// path/to/another/file.ts:45 high Unsanitised user input in 'comment' field could lead to XSS.
function formatFindings(label: string, findings: Findings[]): string {
  if (findings.length === 0) {
    return `${label}: none`;
  }
  const lines: string[] = [];
  findings.forEach((finding) => {
    lines.push(
      `${finding.file}:${finding.line} ${finding.severity} ${finding.description}`
    );
  });

  return `${label}\n${lines.join("\n")}`;
}

// Build LLM message
export function buildUserMessage(
  chunk: DiffChunk,
  securityFindings: Findings[],
  cveFindings: Findings[]
): string {
  const parts: string[] = [];

  if (chunk.totalChunks > 1) {
    parts.push(`Chunk ${chunk.chunkIndex + 1}/${chunk.totalChunks}`);
  }

  parts.push(chunk.diffs.map(formatFileDiff).join("\n\n"));

  parts.push(formatFindings("SECURITY_SCAN", securityFindings));

  parts.push(formatFindings("CVE_SCAN", cveFindings));

  return parts.join("\n\n");
}
