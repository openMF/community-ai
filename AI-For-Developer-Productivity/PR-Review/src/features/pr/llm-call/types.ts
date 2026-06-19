import type { ParsedFileDiff } from "@src/features/pr/git-diff";
import { z } from "zod/v4";

export const SeveritySchema = z.enum(["high", "medium", "low"]);

export const ReviewSchema = z.object({
  file: z.string(),
  line: z.number(),
  problem: z.string(),
  prompt: z.string(),
  severity: SeveritySchema,
  solution: z.string(),
});
export type Review = z.infer<typeof ReviewSchema>;

export const ReviewsSchema = z.object({
  reviews: z.array(ReviewSchema),
});
export type Reviews = Review[];

export interface DiffChunk {
  chunkIndex: number;
  diffs: ParsedFileDiff[];
  totalChunks: number;
}

export interface LLMCallErrorOptions {
  attempts: number;
  cause: unknown;
  retryable: boolean;
}

export class LLMCallError extends Error {
  override readonly cause: unknown;
  readonly attempts: number;
  readonly retryable: boolean;

  constructor(message: string, options: LLMCallErrorOptions) {
    super(message);

    this.name = "LLMCallError";
    this.cause = options.cause;
    this.attempts = options.attempts;
    this.retryable = options.retryable;
  }
}
