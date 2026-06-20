import { getOctokit } from "@actions/github";

export async function getPullRequestDiff(
  token: string,
  owner: string,
  repo: string,
  pullNumber: number
) {
  const octokit = getOctokit(token);
  const response = await octokit.rest.pulls.get({
    headers: { accept: "application/vnd.github.v3.diff" },
    owner,
    pull_number: pullNumber,
    repo,
  });
  return response.data as unknown as string;
}
