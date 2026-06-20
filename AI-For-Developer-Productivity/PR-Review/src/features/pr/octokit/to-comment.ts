import type { Review } from "@src/features/pr/llm-call";
import type { Severity } from "@src/features/pr/security-engine";

const SEV_COLOR: Record<Severity, string> = {
  high: "B60205",
  low: "0075CA",
  medium: "E4A11B",
};

function severityBadge(severity: Severity): string {
  return `![severity: ${severity}](https://img.shields.io/badge/severity-${severity}-${SEV_COLOR[severity]}?style=flat-square)`;
}

// Convert an LLM review into a GitHub review comment.
export const toComment = (review: Review) => {
  const parts: string[] = [
    `${severityBadge(review.severity)} \`${review.file}:${review.line}\``,
    "",
    "---",
    "",
    "**Problem**",
    "",
    review.problem,
  ];

  if (review.solution) {
    parts.push("", "**Solution**", "", review.solution);
  }

  if (review.prompt) {
    parts.push("", "**AI Prompt**", "", "```text", review.prompt, "```");
  }

  return {
    body: parts.join("\n"),
    line: review.line,
    path: review.file,
  };
};
