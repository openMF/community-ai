import * as core from "@actions/core";
import {
  type Reviews,
  ReviewsSchema,
  SYSTEM_PROMPT,
} from "@src/features/pr/llm-call";
import { createLLMClient } from "@src/shared";
import { zodTextFormat } from "openai/helpers/zod";

const MAX_RETRIES = 3;
const INITIAL_RETRY_DELAY_MS = 1000;
const RETRYABLE_STATUS_CODES = new Set([429, 500, 502, 503, 504]);

interface ErrorWithStatus extends Error {
  status: number;
}

// Using 'error is ErrorWithStatus' eliminates the need for inline casting anywhere else
function isRetryableError(error: unknown): error is ErrorWithStatus {
  return (
    error instanceof Error &&
    "status" in error &&
    RETRYABLE_STATUS_CODES.has((error as ErrorWithStatus).status)
  );
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export async function callWithRetry(
  openai: ReturnType<typeof createLLMClient>,
  model: string,
  userMessage: string
): Promise<Reviews> {
  let lastError: unknown;

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const response = await openai.responses.parse({
        input: [
          { content: userMessage, role: "user" },
          { content: SYSTEM_PROMPT, role: "system" },
        ],
        model,
        text: {
          format: zodTextFormat(ReviewsSchema, "reviews"),
        },
      });

      if (!response.output_parsed) {
        throw new Error(
          "LLM returned an empty output payload without parsing errors"
        );
      }

      return response.output_parsed.reviews;
    } catch (error) {
      lastError = error;
      const isRetryable = isRetryableError(error);
      const isLastAttempt = attempt === MAX_RETRIES;

      if (!isRetryable || isLastAttempt) {
        throw new Error(`LLM call failed after ${attempt} attempt(s)`, {
          cause: error,
        });
      }

      const delay = INITIAL_RETRY_DELAY_MS * Math.pow(2, attempt - 1);
      core.warning(`Error in LLM call. Retrying in ${delay}ms.`);
      await sleep(delay);
    }
  }

  // Explicit fallback throw at the bottom
  throw new Error(`LLM call failed after ${MAX_RETRIES} attempts`, {
    cause: lastError,
  });
}
