import * as core from "@actions/core";
import { getOctokit } from "@actions/github";
import {
  type CurrentFinding,
  encodeState,
  type ResolvedFinding,
  type StoredFinding,
  type StoredReviewState,
  SUMMARY_MARKER,
  toComment,
} from "@src/features/pr/octokit";
import { expectError } from "@src/shared";

const RESOLVED_PREFIX =
  "> ~~**Resolved** — this issue was fixed in a later commit.~~\n\n---\n\n";

export async function postReviewComment(
  token: string,
  owner: string,
  repo: string,
  pullNumber: number,
  commitSha: string,
  matched: CurrentFinding[],
  fixed: ResolvedFinding[],
  summary: string,
  summaryCommentId: number | null
): Promise<void> {
  const octokit = getOctokit(token);
  const newFindings: StoredFinding[] = [];

  // To ensure the summary appears at the top, create it first if it doesn't exist.
  let currentSummaryCommentId = summaryCommentId;
  if (currentSummaryCommentId === null) {
    const [err, response] = await expectError(
      octokit.rest.issues.createComment({
        body: `${SUMMARY_MARKER}\n\n_Processing findings..._`,
        issue_number: pullNumber,
        owner,
        repo,
      })
    );
    if (err) {
      const msg = err instanceof Error ? err.message : String(err);
      core.warning(`Failed to create initial summary comment — ${msg}`);
    } else {
      currentSummaryCommentId = response.data.id;
    }
  }

  // Keep existing comment IDs for findings that are still present.
  for (const m of matched) {
    if (m.status !== "active" || !m.previous) {
      continue;
    }
    // Keep the latest file and line information.
    let file: string;
    let line: number;
    if (m.source === "llm") {
      file = m.review.file;
      line = m.review.line;
    } else {
      file = m.finding.file;
      line = m.finding.line;
    }
    newFindings.push({ ...m.previous, file, line });
  }

  // Create review comments for newly detected findings.
  for (const m of matched) {
    if (m.status !== "new") {
      continue;
    }
    if (m.source !== "llm") {
      // Do not post review comments for OSV or scan findings.
      newFindings.push({
        commentId: null,
        file: m.finding.file,
        fingerprint: m.fingerprint,
        line: m.finding.line,
        severity: m.finding.severity,
        source: m.source,
      });
      continue;
    }

    const payload = toComment(m.review);
    const severity = m.review.severity;
    const [err, response] = await expectError(
      octokit.rest.pulls.createReviewComment({
        body: payload.body,
        commit_id: commitSha,
        line: payload.line,
        owner,
        path: payload.path,
        pull_number: pullNumber,
        repo,
        side: "RIGHT",
      })
    );
    if (err) {
      const msg = err instanceof Error ? err.message : String(err);
      core.warning(
        `Failed to post comment for ${payload.path}:${payload.line} — ${msg}`
      );
    } else {
      newFindings.push({
        commentId: response.data.id,
        file: payload.path,
        fingerprint: m.fingerprint,
        line: payload.line,
        severity,
        source: m.source,
      });
    }
  }

  // Mark findings that no longer exist as resolved.
  for (const f of fixed) {
    if (f.previous.commentId === null) {
      continue;
    }
    const [err, response] = await expectError(
      octokit.rest.pulls.getReviewComment({
        comment_id: f.previous.commentId,
        owner,
        repo,
      })
    );
    if (err) {
      const msg = err instanceof Error ? err.message : String(err);
      core.warning(
        `Failed to retrieve comment ${f.previous.commentId} for resolution — ${msg}`
      );
      continue;
    }
    const existing = response.data;
    // Avoid updating a comment that was already marked as resolved.
    if (existing.body.startsWith(RESOLVED_PREFIX)) {
      continue;
    }
    const [updateErr] = await expectError(
      octokit.rest.pulls.updateReviewComment({
        body: RESOLVED_PREFIX + existing.body,
        comment_id: f.previous.commentId,
        owner,
        repo,
      })
    );
    if (updateErr) {
      const msg =
        updateErr instanceof Error ? updateErr.message : String(updateErr);
      core.warning(
        `Failed to resolve comment ${f.previous.commentId} — ${msg}`
      );
    }
  }

  // Persist the latest finding state in the summary comment.
  const newState: StoredReviewState = { findings: newFindings, version: 1 };
  const summaryBody = `${SUMMARY_MARKER}\n\n${summary}${encodeState(newState)}`;
  let upsertErr: unknown;
  if (currentSummaryCommentId !== null) {
    [upsertErr] = await expectError(
      octokit.rest.issues.updateComment({
        body: summaryBody,
        comment_id: currentSummaryCommentId,
        owner,
        repo,
      })
    );
  } else {
    [upsertErr] = await expectError(
      octokit.rest.issues.createComment({
        body: summaryBody,
        issue_number: pullNumber,
        owner,
        repo,
      })
    );
  }
  if (upsertErr) {
    throw new Error("Failed to publish summary comment", { cause: upsertErr });
  }
}
