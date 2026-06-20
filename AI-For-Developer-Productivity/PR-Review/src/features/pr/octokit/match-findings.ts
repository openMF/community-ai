import type { ParsedFileDiff } from "@src/features/pr/git-diff";
import type { Review } from "@src/features/pr/llm-call";
import {
  type CurrentFinding,
  type FindingMatchResult,
  fingerprintLLM,
  fingerprintOSV,
  fingerprintStatic,
  normaliseSnippet,
  type ResolvedFinding,
  type StoredFinding,
  type StoredReviewState,
} from "@src/features/pr/octokit";
import type { Findings } from "@src/features/pr/security-engine";
import stringSimilarity from "string-similarity";

const FUZZY_THRESHOLD = 0.7;

function getLineContent(
  file: string,
  line: number,
  diffs: ParsedFileDiff[]
): string {
  return (
    diffs.find((d) => d.file === file)?.added.find((a) => a.lineNumber === line)
      ?.content ?? ""
  );
}

// Extract package name, version, and vulnerability IDs from an OSV finding description.
// Example: "Added dependency `lodash@4.17.20` has known vulnerabilities: CVE-2021-23337, GHSA-35jh-r3h4-6jhm."
function parseOSVDescription(description: string): {
  osvIds: string[];
  pkgName: string;
  pkgVersion: string;
} {
  const pkg = description.match(/`([^@`]+)@([^`]+)`/);
  const pkgName = pkg?.[1] ?? "unknown";
  const pkgVersion = pkg?.[2] ?? "unknown";

  const idMatches = [
    ...description.matchAll(/\b(CVE-\d{4}-\d+|GHSA-[a-z0-9-]+)\b/gi),
  ];
  const osvIds = idMatches.map((match) => match[0].toUpperCase());

  return {
    osvIds,
    pkgName,
    pkgVersion,
  };
}

// Create an ID for a security rule.
// Security-engine descriptions are deterministic, so a normalised prefix of the description can be used as fingerprint input.
function inferRuleId(description: string): string {
  return description.trim().slice(0, 40).toLowerCase().replace(/\s+/g, "-");
}

// Match vulnerabilities from previous runs.
// Classify findings as:
// - active: finding already exists
// - new: finding was not seen before
// - fixed: finding existed previously but is no longer present
export function matchFindings(
  staticFindings: Findings[],
  osvFindings: Findings[],
  llmReviews: Review[],
  diffs: ParsedFileDiff[],
  previous: StoredReviewState
): FindingMatchResult {
  const previousFindings = new Map<string, StoredFinding>(
    previous.findings.map((finding) => [finding.fingerprint, finding])
  );
  const matchedPrevious = new Set<string>();
  const matched: CurrentFinding[] = [];

  // Find a matching finding from the previous run.
  function findPrevious(fingerprint: string): StoredFinding | undefined {
    const finding = previousFindings.get(fingerprint);
    if (finding) {
      matchedPrevious.add(fingerprint);
    }
    return finding;
  }

  // Match security scan findings.
  for (const finding of staticFindings) {
    const lineContent = getLineContent(finding.file, finding.line, diffs);
    const ruleId = inferRuleId(finding.description);
    const fingerprint = fingerprintStatic(ruleId, finding.file, lineContent);
    const previousFinding = findPrevious(fingerprint);
    matched.push({
      finding,
      fingerprint,
      previous: previousFinding ?? null,
      source: "static",
      status: previousFinding ? "active" : "new",
    });
  }

  // Match dependency vulnerabilities.
  for (const finding of osvFindings) {
    const { osvIds, pkgName, pkgVersion } = parseOSVDescription(
      finding.description
    );
    const fingerprint = fingerprintOSV(pkgName, pkgVersion, osvIds);
    const previousFinding = findPrevious(fingerprint);
    matched.push({
      finding,
      fingerprint,
      previous: previousFinding ?? null,
      source: "osv",
      status: previousFinding ? "active" : "new",
    });
  }

  // Match LLM findings using exact and fuzzy matching.
  for (const review of llmReviews) {
    const lineContent = getLineContent(review.file, review.line, diffs);
    const fingerprint = fingerprintLLM(review.file, lineContent);
    const exactMatch = findPrevious(fingerprint);
    if (exactMatch) {
      matched.push({
        fingerprint,
        previous: exactMatch,
        review,
        source: "llm",
        status: "active",
      });
      continue;
    }

    const normalisedCurrentSnippet = normaliseSnippet(lineContent);

    let bestScore = 0;
    let bestMatch: StoredFinding | null = null;
    // Compare the current snippet against unmatched LLM findings from the previous run and keep the closest match.
    for (const [previousFingerprint, previousFinding] of previousFindings) {
      if (
        matchedPrevious.has(previousFingerprint) ||
        previousFinding.source !== "llm"
      ) {
        continue;
      }

      const prefix = `llm:${previousFinding.file}:`;
      const previousSnippet = previousFingerprint.startsWith(prefix)
        ? previousFingerprint.slice(prefix.length)
        : "";

      const score = stringSimilarity.compareTwoStrings(
        normalisedCurrentSnippet,
        previousSnippet
      );
      if (score > bestScore) {
        bestScore = score;
        bestMatch = previousFinding;
      }
    }

    // Treat highly similar snippets as the same finding.
    if (bestScore >= FUZZY_THRESHOLD && bestMatch) {
      matchedPrevious.add(bestMatch.fingerprint);
      matched.push({
        fingerprint,
        previous: bestMatch,
        review,
        source: "llm",
        status: "active",
      });
      continue;
    }
    matched.push({
      fingerprint,
      previous: null,
      review,
      source: "llm",
      status: "new",
    });
  }

  // Any previous finding that wasn't matched in this run is considered fixed.
  const fixed: ResolvedFinding[] = [];
  for (const [fingerprint, previousFinding] of previousFindings) {
    if (!matchedPrevious.has(fingerprint)) {
      fixed.push({
        previous: previousFinding,
      });
    }
  }

  return {
    fixed,
    matched,
  };
}
