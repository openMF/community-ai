import type { ParsedFileDiff } from "@src/features/pr/git-diff";
import {
  buildUserMessage,
  callWithRetry,
  chunkDiffs,
  createFindingsTable,
  getRelevantChunkFindings,
  type Reviews,
} from "@src/features/pr/llm-call";
import type { Findings } from "@src/features/pr/security-engine";
import { createLLMClient, expectError, getConfig } from "@src/shared";
import pLimit from "p-limit";

const MAX_CONCURRENT_CHUNKS = 3;

export async function callLLM(
  diffs: ParsedFileDiff[],
  securityFindings: Findings[],
  cveFindings: Findings[],
  apiKey: string
): Promise<Reviews> {
  // LLM setup
  const openai = createLLMClient(apiKey);
  const model = getConfig().model || "gpt-5-nano";

  // Prepare review context
  const chunks = chunkDiffs(diffs);
  const securityLookupTable = createFindingsTable(securityFindings);
  const cveLookupTable = createFindingsTable(cveFindings);

  // Small PR → single request
  if (chunks.length === 1) {
    const chunk = chunks[0]!;
    const message = buildUserMessage(
      chunk,
      getRelevantChunkFindings(chunk, securityLookupTable),
      getRelevantChunkFindings(chunk, cveLookupTable)
    );
    const [error, result] = await expectError(
      callWithRetry(openai, model, message)
    );
    if (error) {
      throw new Error("AI review failed", { cause: error });
    }
    return result;
  }

  // Large PR → process chunks concurrently
  const limit = pLimit(MAX_CONCURRENT_CHUNKS);
  const results = await Promise.all(
    chunks.map((chunk) =>
      limit(async () => {
        const message = buildUserMessage(
          chunk,
          getRelevantChunkFindings(chunk, securityLookupTable),
          getRelevantChunkFindings(chunk, cveLookupTable)
        );
        const [error, result] = await expectError(
          callWithRetry(openai, model, message)
        );
        if (error) {
          throw new Error("AI review failed", {
            cause: error,
          });
        }
        return result;
      })
    )
  );

  // Merge and deduplicate reviews
  const seen = new Set<string>();
  const reviews = results.flat().filter((review) => {
    const key = `${review.file}:${review.line}:${review.problem}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });

  return reviews;
}
