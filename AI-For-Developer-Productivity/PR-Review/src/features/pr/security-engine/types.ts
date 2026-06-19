import type { SeveritySchema } from "@src/features/pr/llm-call";
import { z } from "zod/v4";

export type Severity = z.infer<typeof SeveritySchema>;

export interface SecurityRule {
  description: string;
  fileExtensions?: string[];
  id: string;
  pattern: RegExp;
  severity: Severity;
}

export interface Findings {
  description: string;
  file: string;
  line: number;
  severity: Severity;
}
