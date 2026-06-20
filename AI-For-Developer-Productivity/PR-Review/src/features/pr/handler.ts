import { checkVulnerabilities } from "@src/features/pr/cve-detection";
import { parseGitDiff } from "@src/features/pr/git-diff";
import { callLLM } from "@src/features/pr/llm-call";
import {
  generateSummary,
  getPullRequestDiff,
  loadState,
  matchFindings,
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
  // Load findings from the previous run so we can determine which findings are new, active, or resolved.
  const [loadError, loadedReviewState] = await expectError(
    loadState(token, owner, repo, prNumber)
  );
  if (loadError) {
    throw new Error("Failed to load previous state from summary", {
      cause: loadError,
    });
  }

  // Fetch the raw git diff for this pull request.
  const [diffError, rawDiff] = await expectError(
    getPullRequestDiff(token, owner, repo, prNumber)
  );
  if (diffError) {
    throw new Error("Failed to fetch raw git diff from GitHub API", {
      cause: diffError,
    });
  }

  // Convert the git diff into a structured format.
  const parsedDiff = parseGitDiff(rawDiff);
  if (parsedDiff.length === 0) {
    return null;
  }

  // Scan newly added dependencies for known vulnerabilities.
  const [dependencyError, dependencyScan] = await expectError(
    checkVulnerabilities(parsedDiff)
  );
  if (dependencyError) {
    throw new Error("Dependency vulnerability scan failed", {
      cause: dependencyError,
    });
  }

  // Run regex based security rules.
  const securityScan = runSecurityEngine(parsedDiff);

  // Run LLM review.
  const [llmError, llmReviews] = await expectError(
    callLLM(parsedDiff, securityScan, dependencyScan, apiKey)
  );
  if (llmError) {
    throw new Error("Failed to generate review comments", {
      cause: llmError,
    });
  }

  // Compare current findings against the previous run and classify them as new, active, or resolved.
  const { fixed, matched } = matchFindings(
    securityScan,
    dependencyScan,
    llmReviews,
    parsedDiff,
    loadedReviewState.state
  );

  // Build the PR summary comment.
  const summary = generateSummary(matched, fixed);

  return {
    fixed,
    matched,
    summary,
    summaryCommentId: loadedReviewState.summaryCommentId,
  };
}
