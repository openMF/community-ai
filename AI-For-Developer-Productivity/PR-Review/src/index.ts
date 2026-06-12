import * as core from "@actions/core";
import * as github from "@actions/github";
import { handlePullRequest } from "@src/features/pr/handler";
import { postReviewComment } from "@src/features/pr/octokit";
import { expectError } from "@src/shared";

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

  const [analysisError, result] = await expectError(
    handlePullRequest({ apiKey, owner, prNumber: pr.number, repo, token })
  );
  if (analysisError) {
    core.error(`Security analysis failed: ${analysisError.message}`);
    core.setFailed(analysisError.message);
    return;
  }
  if (!result || (result.comments.length === 0 && !result.summary)) {
    return;
  }

  const [postError] = await expectError(
    postReviewComment(
      token,
      owner,
      repo,
      pr.number,
      result.comments,
      result.summary
    )
  );
  if (postError) {
    core.error(`Failed to publish review comments: ${postError.message}`);
    core.setFailed(postError.message);
    return;
  }
}

run();
