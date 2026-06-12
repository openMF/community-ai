import * as core from "@actions/core";
import {
  LLMCallError,
  type Reviews,
  ReviewsSchema,
  SYSTEM_PROMPT,
} from "@src/features/pr/llm-call";
import { createLLMClient } from "@src/shared";
import { zodTextFormat } from "openai/helpers/zod";

const MAX_RETRIES = 3;
const INITIAL_RETRY_DELAY_MS = 1000;

const RETRYABLE_STATUS_CODES = new Set([429, 500, 502, 503, 504]);

function isRetryableError(error: unknown): boolean {
  if (error instanceof Error && "status" in error) {
    return RETRYABLE_STATUS_CODES.has((error as { status: number }).status);
  }
  return false;
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
          {
            content: SYSTEM_PROMPT,
            role: "system",
          },
          {
            content: userMessage,
            role: "user",
          },
        ],
        model,
        text: {
          format: zodTextFormat(ReviewsSchema, "reviews"),
        },
      });
      if (!response.output_parsed) {
        throw new LLMCallError("LLM returned empty output", {
          attempts: attempt,
          cause: null,
          retryable: false,
        });
      }
      return response.output_parsed;
    } catch (error) {
      lastError = error;
      if (!isRetryableError(error) || attempt === MAX_RETRIES) {
        throw new LLMCallError(`LLM call failed after ${attempt} attempt(s)`, {
          attempts: attempt,
          cause: error,
          retryable: isRetryableError(error),
        });
      }
      const delay = INITIAL_RETRY_DELAY_MS * Math.pow(2, attempt - 1);
      core.warning(`Error in LLM call. Retrying in ${delay}ms.`);
      await sleep(delay);
    }
  }

  throw new LLMCallError(`LLM call failed after ${MAX_RETRIES} attempts`, {
    attempts: MAX_RETRIES,
    cause: lastError,
    retryable: false,
  });
}
