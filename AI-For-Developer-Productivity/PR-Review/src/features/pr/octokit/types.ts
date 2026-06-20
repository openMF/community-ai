import type { Review } from "@src/features/pr/llm-call";
import type { Findings, Severity } from "@src/features/pr/security-engine";

export interface StoredFinding {
  commentId: number | null; // PR comment ID for this finding.
  file: string;
  fingerprint: string; // Stable identifier used across runs.
  line: number;
  severity: Severity;
  source: "static" | "osv" | "llm";
}

export interface StoredReviewState {
  findings: StoredFinding[];
  version: 1;
}

export interface LoadedReviewState {
  state: StoredReviewState;
  summaryCommentId: number | null;
}

export type FindingStatus = "new" | "active";

// Current finding linked to previously stored state.
export type CurrentFinding =
  | {
      finding: Findings;
      fingerprint: string;
      previous: StoredFinding | null;
      source: "static" | "osv";
      status: FindingStatus;
    }
  | {
      fingerprint: string;
      previous: StoredFinding | null;
      review: Review;
      source: "llm";
      status: FindingStatus;
    };

// Previously stored finding that no longer exists.
export interface ResolvedFinding {
  previous: StoredFinding;
}

export interface FindingMatchResult {
  fixed: ResolvedFinding[];
  matched: CurrentFinding[];
}

export interface SummaryRow {
  file: string;
  line: number;
  problem: string;
  severity: Severity;
  status: "new" | "active";
}
