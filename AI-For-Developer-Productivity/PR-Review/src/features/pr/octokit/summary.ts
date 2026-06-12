import type { Review } from "@src/features/pr/llm-call";

export const BADGES = {
  clean:
    "![Clean](https://img.shields.io/badge/Security-Clean-2ea44f?style=for-the-badge)",
  high: "![High](https://img.shields.io/badge/Severity-High-d73a4a?style=flat-square)",
  issues:
    "![Issues Found](https://img.shields.io/badge/Security-Issues_Found-d73a4a?style=for-the-badge)",
  low: "![Low](https://img.shields.io/badge/Severity-Low-0366d6?style=flat-square)",
  medium:
    "![Medium](https://img.shields.io/badge/Severity-Medium-fb8532?style=flat-square)",
} as const;

const severityWeight: Record<Review["severity"], number> = {
  high: 3,
  low: 1,
  medium: 2,
};

export function generateSummary(reviews: Review[]): string {
  const highCount = reviews.filter(
    (review) => review.severity === "high"
  ).length;

  const mediumCount = reviews.filter(
    (review) => review.severity === "medium"
  ).length;

  const lowCount = reviews.filter((review) => review.severity === "low").length;

  const total = reviews.length;

  let body = "## 🛡️ Security Review Summary\n\n";

  if (total === 0) {
    body += `${BADGES.clean}\n\n`;
    body += "> No security issues were detected in the analyzed changes.\n";

    return body;
  }

  body += `${BADGES.issues}\n\n`;
  body +=
    `> The security review identified **${total}** potential security ` +
    `finding${total === 1 ? "" : "s"}. Findings are sorted by severity and ` +
    `should be reviewed before merging.\n\n`;

  body += "### Summary\n\n";
  body += "| Severity | Count |\n";
  body += "| :--- | ---: |\n";

  if (highCount > 0) {
    body += `| ${BADGES.high} | **${highCount}** |\n`;
  }

  if (mediumCount > 0) {
    body += `| ${BADGES.medium} | **${mediumCount}** |\n`;
  }

  if (lowCount > 0) {
    body += `| ${BADGES.low} | **${lowCount}** |\n`;
  }

  body += "\n";
  body += "### Detailed Findings\n\n";
  body += "| Severity | File | Line | Issue |\n";
  body += "| :--- | :--- | ---: | :--- |\n";

  const sortedReviews = [...reviews].sort(
    (a, b) => severityWeight[b.severity] - severityWeight[a.severity]
  );

  for (const review of sortedReviews) {
    const badge = BADGES[review.severity];
    const fileRef = `\`${review.file.replace(/\|/g, "\\|")}\``;
    const safeComment = review.comment
      .replace(/\n/g, " ")
      .replace(/\|/g, "\\|")
      .trim();
    body += `| ${badge} | ${fileRef} | ${review.line} | ${safeComment} |\n`;
  }

  return body;
}
