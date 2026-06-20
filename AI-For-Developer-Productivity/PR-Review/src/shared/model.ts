import OpenAI from "openai";

export function createLLMClient(apiKey: string) {
  return new OpenAI({
    apiKey,
  });
}
