import type { Review } from "@src/features/pr/llm-call";
import type { Severity } from "@src/features/pr/security-engine";

const SEV_COLOR: Record<Severity, string> = {
  high: "B60205",
  low: "0075CA",
  medium: "E4A11B",
};

function severityBadge(sev: Severity): string {
  return `![severity: ${sev}](https://img.shields.io/badge/severity-${sev}-${SEV_COLOR[sev]}?style=flat-square)`;
}

export const toComment = (r: Review) => {
  const parts: string[] = [
    `${severityBadge(r.severity)} \`${r.file}:${r.line}\``,
    "",
    "---",
    "",
    "**Problem**",
    "",
    r.problem,
  ];

  if (r.solution) {
    parts.push("", "**Solution**", "", r.solution);
  }

  if (r.prompt) {
    parts.push("", "**AI Prompt**", "", "```text", r.prompt, "```");
  }

  return {
    body: parts.join("\n"),
    line: r.line,
    path: r.file,
  };
};
