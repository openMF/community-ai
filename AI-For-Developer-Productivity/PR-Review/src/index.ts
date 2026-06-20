import * as core from "@actions/core";
import * as github from "@actions/github";
import { handlePullRequest } from "@src/features/pr/handler";
import { postReviewComment } from "@src/features/pr/octokit";
import { expectError, failAction } from "@src/shared";

async function run() {
  const token = core.getInput("github-token");
  const apiKey = core.getInput("openai-api-key");

  const { context } = github;
  if (context.eventName !== "pull_request") {
    core.notice(
      `Triggered by '${context.eventName}' event but this action only runs on pull requests.`
    );
    return;
  }

  const pr = context.payload.pull_request;
  if (!pr) {
    core.error("Pull request payload was not found.");
    core.setFailed("No pull request found in the GitHub context.");
    return;
  }

  const { owner, repo } = context.repo;
  const commitSha = pr["head"].sha as string;

  const [analysisError, result] = await expectError(
    handlePullRequest({ apiKey, owner, prNumber: pr.number, repo, token })
  );
  if (analysisError) {
    failAction("Security analysis failed", analysisError);
    return;
  }
  if (!result || (result.matched.length === 0 && result.fixed.length === 0)) {
    core.warning("Nothing to post about. No findings or comment to update.");
    return;
  }

  const [postError] = await expectError(
    postReviewComment(
      token,
      owner,
      repo,
      pr.number,
      commitSha,
      result.matched,
      result.fixed,
      result.summary,
      result.summaryCommentId
    )
  );
  if (postError) {
    failAction("Failed to publish review comments", postError);
    return;
  }
}

run();
