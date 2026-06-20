import type {
  CurrentFinding,
  ResolvedFinding,
  SummaryRow,
} from "@src/features/pr/octokit";
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

function extractRow(m: CurrentFinding): SummaryRow | null {
  if (m.source === "llm") {
    return {
      file: m.review.file,
      line: m.review.line,
      problem: m.review.problem,
      severity: m.review.severity,
      status: m.status as "new" | "active",
    };
  }
  return {
    file: m.finding.file,
    line: m.finding.line,
    problem: m.finding.description,
    severity: m.finding.severity,
    status: m.status as "new" | "active",
  };
}

// Generate the PR summary comment.
// Displays current findings and tracks findings that are new, active, or fixed compared to the previous run.
export function generateSummary(
  matched: CurrentFinding[],
  fixed: ResolvedFinding[]
): string {
  const rows = matched
    .map(extractRow)
    .filter((r): r is SummaryRow => r !== null);
  const newCount = matched.filter((m) => m.status === "new").length;
  const activeCount = matched.filter((m) => m.status === "active").length;
  const fixedCount = fixed.length;
  const total = rows.length;

  if (total === 0 && fixedCount === 0) {
    return [
      "## Security Review",
      "",
      STATUS_CLEAN,
      "",
      "---",
      "",
      "> No security issues were detected in the analysed changes.",
      "",
    ].join("\n");
  }

  const severities: Severity[] = ["high", "medium", "low"];
  const counts: Record<Severity, number> = { high: 0, low: 0, medium: 0 };
  for (const r of rows) counts[r.severity]++;

  const statusRows = [
    `    <tr><td>New</td><td><strong>${newCount}</strong></td></tr>`,
    `    <tr><td>Active</td><td><strong>${activeCount}</strong></td></tr>`,
    `    <tr><td>Fixed</td><td><strong>${fixedCount}</strong></td></tr>`,
  ].join("\n");

  const summaryRows = severities
    .filter((s) => counts[s] > 0)
    .map(
      (s) =>
        `    <tr><td>${severityBadge(s)}</td><td><strong>${counts[s]}</strong></td></tr>`
    )
    .join("\n");

  const sortedRows = [...rows].sort(
    (a, b) => severityWeight[b.severity] - severityWeight[a.severity]
  );

  const findingRows = sortedRows
    .map((r) => {
      const location = `<code>${r.file}:${r.line}</code>`;
      const issue = r.problem.replace(/\n/g, " ").trim();

      const status = r.status === "new" ? "New" : "Active";

      return `    <tr><td>${severityBadge(r.severity)}</td><td>${location}</td><td>${issue}</td><td>${status}</td></tr>`;
    })
    .join("\n");

  const intro =
    total > 0
      ? `> **${total} finding${total === 1 ? "" : "s"}** detected` +
        (newCount > 0 ? ` (${newCount} new)` : "") +
        `. Review and resolve issues before merging.`
      : `> All previously reported findings have been resolved.`;

  return [
    "## Security Review",
    "",
    total > 0 ? STATUS_ISSUES : STATUS_CLEAN,
    "",
    "---",
    "",
    intro,
    "",
    "### Status",
    "",
    "<table>",
    "  <thead>",
    "    <tr>",
    '      <th width="50%">State</th>',
    '      <th width="50%">Count</th>',
    "    </tr>",
    "  </thead>",
    "  <tbody>",
    statusRows,
    "  </tbody>",
    "</table>",
    "",
    ...(total > 0
      ? [
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
          '      <th width="20%">Severity</th>',
          '      <th width="25%">Location</th>',
          '      <th width="45%">Issue</th>',
          '      <th width="10%">State</th>',
          "    </tr>",
          "  </thead>",
          "  <tbody>",
          findingRows,
          "  </tbody>",
          "</table>",
          "",
        ]
      : []),
  ].join("\n");
}
