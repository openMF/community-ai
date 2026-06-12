import { getOctokit } from "@actions/github";

export async function postReviewComment(
  token: string,
  owner: string,
  repo: string,
  pullNumber: number,
  comments: { body: string; line: number; path: string }[],
  summary: string
) {
  const octokit = getOctokit(token);

  const payload = {
    body: summary,
    event: "COMMENT" as const,
    owner,
    pull_number: pullNumber,
    repo,
    ...(comments.length > 0 && {
      comments: comments.map((c) => ({
        body: c.body,
        line: c.line,
        path: c.path,
      })),
    }),
  };

  await octokit.rest.pulls.createReview(payload);
}
