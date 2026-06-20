import { getOctokit } from "@actions/github";
import type {
  LoadedReviewState,
  StoredReviewState,
} from "@src/features/pr/octokit";

export const SUMMARY_MARKER = "<!-- summary -->";
const STATE_OPEN = "<!-- state"; // Hidden block used to store state inside the summary comment.
const STATE_CLOSE = "-->";
// Empty state used on the first run or when state cannot be loaded.
export const EMPTY_STATE: StoredReviewState = {
  findings: [],
  version: 1,
};

// Read the hidden state block from a summary comment.
function decodeState(body: string): StoredReviewState | null {
  try {
    // Find the start of the hidden state block.
    const stateStart = body.indexOf(STATE_OPEN);
    if (stateStart === -1) {
      return null;
    }

    // State content starts on the line after "<!-- state".
    const contentStart = body.indexOf("\n", stateStart) + 1;
    // Find the closing "-->" marker.
    const stateEnd = body.indexOf(STATE_CLOSE, contentStart);
    if (stateEnd === -1) {
      return null;
    }

    // Extract the Base64-encoded state.
    const encodedState = body.slice(contentStart, stateEnd).trim();
    // Decode Base64 back into JSON.
    const decodedState = Buffer.from(encodedState, "base64").toString("utf-8");
    // Parse the JSON into our state object.
    const state = JSON.parse(decodedState) as StoredReviewState;
    // Validate the expected shape.
    if (state.version !== 1 || !Array.isArray(state.findings)) {
      return null;
    }

    return state;
  } catch {
    return null;
  }
}

// Convert state into a Base64 block that can be embedded in the PR comment.
export function encodeState(state: StoredReviewState): string {
  const serializedState = JSON.stringify(state);
  const encodedState = Buffer.from(serializedState, "utf-8").toString("base64");
  return ["", STATE_OPEN, encodedState, STATE_CLOSE].join("\n");
}

// Load the previous Review Owl state from the PR summary comment.
export async function loadState(
  token: string,
  owner: string,
  repo: string,
  pullNumber: number
): Promise<LoadedReviewState> {
  const octokit = getOctokit(token);

  // Fetch all issue comments on the pull request.
  const { data: comments } = await octokit.rest.issues.listComments({
    issue_number: pullNumber,
    owner,
    per_page: 100,
    repo,
  });

  // Find the Review Owl summary comment.
  const summaryComment = comments.find((comment) =>
    comment.body?.includes(SUMMARY_MARKER)
  );

  // First run thus no summary comment exists yet.
  if (!summaryComment?.body) {
    return {
      state: EMPTY_STATE,
      summaryCommentId: null,
    };
  }

  return {
    // Load stored findings from the hidden state block.
    state: decodeState(summaryComment.body) ?? EMPTY_STATE,
    // Save the comment ID so we can update this comment later.
    summaryCommentId: summaryComment.id,
  };
}
