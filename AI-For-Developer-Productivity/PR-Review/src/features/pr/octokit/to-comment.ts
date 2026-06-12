import type { Review } from "@src/features/pr/llm-call";
import { BADGES } from "@src/features/pr/octokit";

export const toComment = (f: Review) => ({
  body: `${BADGES[f.severity]}\n\n${f.comment}`,
  line: f.line,
  path: f.file,
});
