import type { ParsedFileDiff } from "@src/features/pr/git-diff";
import { z } from "zod/v4";

export const SeveritySchema = z.enum(["high", "medium", "low"]);

export const ReviewSchema = z.object({
  file: z
    .string()
    .describe(
      "The exact file path where the security vulnerability was discovered, taken directly from the diff."
    ),
  line: z
    .number()
    .describe(
      "The specific line number in the newly added code where the vulnerability exists."
    ),
  problem: z.string().describe(
    "A detailed explanation of the security vulnerability, the technical risk it introduces, and how it could be exploited."
  ),
  prompt: z
    .string()
    .describe(
      "A direct, precise technical prompt instructing another AI model exactly how to refactor and fix this vulnerability safely."
    ),
  severity: SeveritySchema.describe(
    "The impact level of the vulnerability: 'high' for RCE/Auth bypass, 'medium' for conditional exploits, or 'low' for defense-in-depth issues."
  ),
  solution: z
    .string()
    .describe(
      "A step-by-step fix guide including a real, secure code replacement wrapped in markdown code blocks. Avoid pseudocode."
    ),
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
