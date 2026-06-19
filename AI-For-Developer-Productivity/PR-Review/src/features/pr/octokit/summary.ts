import type { Review } from "@src/features/pr/llm-call";
import type { Severity } from "@src/features/pr/security-engine";

const SEV_COLOR: Record<Severity, string> = {
  high: "B60205",
  low: "0075CA",
  medium: "E4A11B",
};

function severityBadge(sev: Severity): string {
  return `<img src="https://img.shields.io/badge/severity-${sev}-${SEV_COLOR[sev]}?style=flat-square" alt="severity: ${sev}">`;
}

const STATUS_CLEAN =
  "![security: clean](https://img.shields.io/badge/security-clean-2EA44F?style=flat-square)";
const STATUS_ISSUES =
  "![security: issues found](https://img.shields.io/badge/security-issues_found-B60205?style=flat-square)";

const severityWeight: Record<Severity, number> = { high: 3, low: 1, medium: 2 };

export function generateSummary(reviews: Review[]): string {
  const total = reviews.length;
  const counts: Record<Severity, number> = { high: 0, low: 0, medium: 0 };
  for (const r of reviews) counts[r.severity]++;

  if (total === 0) {
    return [
      "## Security Review",
      "",
      STATUS_CLEAN,
      "",
      "---",
      "",
      "> No security issues were detected in the analyzed changes.",
      "",
    ].join("\n");
  }

  const severities: Severity[] = ["high", "medium", "low"];

  const summaryRows = severities
    .filter((s) => counts[s] > 0)
    .map(
      (s) =>
        `    <tr><td>${severityBadge(s)}</td><td><strong>${counts[s]}</strong></td></tr>`
    )
    .join("\n");

  const sortedReviews = [...reviews].sort(
    (a, b) => severityWeight[b.severity] - severityWeight[a.severity]
  );

  const findingRows = sortedReviews
    .map((r) => {
      const location = `<code>${r.file}:${r.line}</code>`;
      const issue = r.problem.replace(/\n/g, " ").trim();
      return `    <tr><td>${severityBadge(r.severity)}</td><td>${location}</td><td>${issue}</td></tr>`;
    })
    .join("\n");

  return [
    "## Security Review",
    "",
    STATUS_ISSUES,
    "",
    "---",
    "",
    `> **${total} finding${total === 1 ? "" : "s"}** identified.` +
    " Resolve all high-severity issues before merging.",
    "",
    "### Summary",
    "",
    "<table>",
    "  <thead>",
    "    <tr>",
    '      <th width="50%">Severity</th>',
    '      <th width="50%">Count</th>',
    "    </tr>",
    "  </thead>",
    "  <tbody>",
    summaryRows,
    "  </tbody>",
    "</table>",
    "",
    "### Findings",
    "",
    "<table>",
    "  <thead>",
    "    <tr>",
    '      <th width="25%">Severity</th>',
    '      <th width="25%">Location</th>',
    '      <th width="50%">Issue</th>',
    "    </tr>",
    "  </thead>",
    "  <tbody>",
    findingRows,
    "  </tbody>",
    "</table>",
    "",
  ].join("\n");
}
