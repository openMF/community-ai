import type { ParsedFileDiff } from "@src/features/pr/git-diff";
import type { DiffChunk, Review, Reviews } from "@src/features/pr/llm-call";
import { encodingForModel } from "js-tiktoken";

const MAX_TOKENS_PER_CHUNK = 10000;

// Estimates the token cost of a single file diff.
export function countFileTokens(file: ParsedFileDiff): number {
  // Build the same formatted text we'll eventually send to the LLM
  const lines = [
    `FILE ${file.file}`,
    ...file.changes.map(
      (line) => `${line.prefix}${line.lineNumber} ${line.content}`
    ),
  ];
  const encoder = encodingForModel("gpt-5-nano");
  return encoder.encode(lines.join("\n")).length;
}

export function chunkDiffs(diffs: ParsedFileDiff[]): DiffChunk[] {
  const chunks: ParsedFileDiff[][] = [];
  let currentChunk: ParsedFileDiff[] = [];
  let currentTokens = 0;
  diffs.forEach((file) => {
    const fileTokens = countFileTokens(file);
    // Start a new chunk if this file would exceed the limit.
    if (
      currentTokens + fileTokens > MAX_TOKENS_PER_CHUNK &&
      currentChunk.length > 0
    ) {
      chunks.push(currentChunk);
      currentChunk = [];
      currentTokens = 0;
    }
    currentChunk.push(file);
    currentTokens += fileTokens;
  });

  // Add the final chunk.
  if (currentChunk.length > 0) {
    chunks.push(currentChunk);
  }

  // Include chunk metadata.
  return chunks.map((diffs, index) => ({
    chunkIndex: index,
    diffs,
    totalChunks: chunks.length,
  }));
}

// Build lookup table
// file -> findings
export function createFindingsTable(findings: Reviews): Map<string, Review[]> {
  const index = new Map<string, Review[]>();

  findings.reviews.forEach((review) => {
    const existing = index.get(review.file);
    if (existing) {
      existing.push(review);
      return;
    }
    index.set(review.file, [review]);
  });

  return index;
}

// Get only findings relevant to files in this chunk
export function getRelevantChunkFindings(
  chunk: DiffChunk,
  findingsIndex: Map<string, Review[]>
): Reviews {
  const reviews: Review[] = [];

  chunk.diffs.forEach((diff) => {
    const fileReviews = findingsIndex.get(diff.file);
    if (!fileReviews) {
      return;
    }
    reviews.push(...fileReviews);
  });

  return { reviews };
}
