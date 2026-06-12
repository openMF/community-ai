import type { ParsedFileDiff } from "@src/features/pr/git-diff";
import type { DiffChunk, Reviews } from "@src/features/pr/llm-call";

// Security review instructions
export const SYSTEM_PROMPT = `You are a security code reviewer.

Tasks:
- Find security vulnerabilities missed by automated scans.
- Validate provided findings and ignore false positives.
- Assess vulnerable dependencies.
- Report new security issues.

Focus:
- Injection (SQL, XSS, command, LDAP, template)
- Auth/Authz (IDOR, privilege escalation, session flaws)
- Sensitive data exposure
- Cryptography misuse
- Business logic flaws
- Vulnerable dependencies
- Unsafe deserialisation
- SSRF and path traversal

Rules:
- Report only issues in added lines.
- Use the exact diff line number.
- Ignore style, quality, and performance issues.
- Avoid speculation.
- Return only valid JSON.

Schema:
{
  "reviews": [
    {
      "file": "path/to/file",
      "line": 42,
      "severity": "high|medium|low",
      "comment": "Issue and fix"
    }
  ]
}

If nothing is found:
{"reviews":[]}`;

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
function formatFindings(label: string, findings: Reviews): string {
  if (findings.reviews.length === 0) {
    return `${label}: none`;
  }
  const lines: string[] = [];
  findings.reviews.forEach((review) => {
    lines.push(
      `${review.file}:${review.line} ${review.severity} ${review.comment}`
    );
  });

  return `${label}\n${lines.join("\n")}`;
}

// Build LLM message
export function buildUserMessage(
  chunk: DiffChunk,
  securityFindings: Reviews,
  cveFindings: Reviews
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
