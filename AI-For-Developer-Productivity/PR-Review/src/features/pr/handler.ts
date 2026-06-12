import * as core from "@actions/core";
import { checkVulnerabilities } from "@src/features/pr/cve-detection";
import { parseGitDiff } from "@src/features/pr/git-diff";
import { callLLM, LLMCallError } from "@src/features/pr/llm-call";
import {
  generateSummary,
  getPullRequestDiff,
  toComment,
} from "@src/features/pr/octokit";
import { runSecurityEngine } from "@src/features/pr/security-engine";
import { expectError } from "@src/shared";

export async function handlePullRequest({
  apiKey,
  owner,
  prNumber,
  repo,
  token,
}: {
  apiKey: string;
  owner: string;
  prNumber: number;
  repo: string;
  token: string;
}) {
  const [diffError, rawDiff] = await expectError(
    getPullRequestDiff(token, owner, repo, prNumber)
  );
  if (diffError) {
    throw new Error("Failed to fetch pull request diff.");
  }

  const parsedDiff = parseGitDiff(rawDiff);
  if (parsedDiff.length === 0) {
    return null;
  }

  // Check for dependency vulnerabilities
  const [dependencyError, dependencyScanResult] = await expectError(
    checkVulnerabilities(parsedDiff)
  );
  if (dependencyError) {
    core.warning("Dependency vulnerability scan failed.");
    core.debug(String(dependencyError));
  }
  const dependencyScan = dependencyScanResult ?? { reviews: [] };

  // Regex based security scan
  const securityScan = runSecurityEngine(parsedDiff);

  // LLM Review
  const [llmError, llmReviewResult] = await expectError(
    callLLM(parsedDiff, securityScan, dependencyScan, apiKey)
  );
  if (llmError) {
    if (llmError instanceof LLMCallError) {
      core.warning("AI review encountered an unexpected error.");
      core.debug(
        JSON.stringify({
          cause: llmError.cause,
          message: llmError.message,
          retryable: llmError.retryable,
        })
      );
    } else {
      core.warning("AI review encountered an unexpected error.");
      core.debug(String(llmError));
    }
  }
  const llmReview = llmReviewResult ?? { reviews: [] };
  const allReviews = [
    ...dependencyScan.reviews,
    ...securityScan.reviews,
    ...llmReview.reviews,
  ];

  return {
    comments: allReviews.map(toComment),
    summary: generateSummary(allReviews),
  };
}
