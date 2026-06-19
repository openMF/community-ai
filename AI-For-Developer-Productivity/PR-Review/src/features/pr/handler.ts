import { checkVulnerabilities } from "@src/features/pr/cve-detection";
import { parseGitDiff } from "@src/features/pr/git-diff";
import { callLLM } from "@src/features/pr/llm-call";
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
    const details = diffError instanceof Error ? diffError.message : String(diffError);
    throw new Error(`Failed to fetch pull request diff: ${details}`);
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
    const details = dependencyError instanceof Error ? dependencyError.message : String(dependencyError);
    throw new Error(`Dependency vulnerability scan failed: ${details}`);
  }
  const dependencyScan = dependencyScanResult ?? [];

  // Regex based security scan
  const securityScan = runSecurityEngine(parsedDiff);

  // LLM Review
  const [llmError, LLMReviews] = await expectError(
    callLLM(parsedDiff, securityScan, dependencyScan, apiKey)
  );
  if (llmError) {
    const details = llmError instanceof Error ? llmError.message : String(llmError);
    throw new Error(`AI review encountered an unexpected error: ${details}`);
  }
  if (LLMReviews) {
    return {
      comments: LLMReviews.map(toComment),
      summary: generateSummary(LLMReviews),
    };
  }
}
