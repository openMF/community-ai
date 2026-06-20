import type { ParsedFileDiff } from "@src/features/pr/git-diff";
import type { DiffChunk } from "@src/features/pr/llm-call";

import type { Findings } from "../security-engine";

// Security review instructions
export const SYSTEM_PROMPT = `
Expert Application Security reviewer.

Review ONLY added code from the diff.

Report ONLY:
- Real vulnerabilities introduced by the diff
- Verified dependency vulnerabilities
- Valid security scanner findings

Do NOT report:
- Style issues
- Code quality issues without security impact
- Best practices
- Speculation
- Potential issues without evidence
- False positives

Focus on:
SQL Injection, Command Injection, XSS, SSRF, Path Traversal,
LDAP Injection, Template Injection, Unsafe Deserialization,
Authentication flaws, Authorization flaws, IDOR,
Privilege Escalation, Session Management flaws,
Sensitive Data Exposure, Cryptography misuse,
Business Logic vulnerabilities, Vulnerable Dependencies.

Requirements:
- Use exact added diff line numbers.
- Base findings only on evidence visible in the diff.
- Do not assume protections or missing protections.
- If exploitation cannot be reasonably inferred, do not report.
- Prefer false negatives over false positives.

Use technical English.
Be direct, precise, and actionable.
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
