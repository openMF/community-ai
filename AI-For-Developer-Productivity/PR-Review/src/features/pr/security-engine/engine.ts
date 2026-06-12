import type { ParsedFileDiff } from "@src/features/pr/git-diff";
import type { Review, Reviews } from "@src/features/pr/llm-call";
import {
  rules as defaultRules,
  type SecurityRule,
} from "@src/features/pr/security-engine";
import { getConfig } from "@src/shared";

export function runSecurityEngine(diffs: ParsedFileDiff[]): Reviews {
  const reviews: Review[] = [];
  const config = getConfig();
  const allRules: SecurityRule[] = [...defaultRules];

  if (config.rules) {
    for (const rule of config.rules) {
      allRules.push({
        description: rule.description,
        fileExtensions: rule.fileExtensions,
        id: rule.id,
        pattern: new RegExp(rule.pattern),
        severity: rule.severity,
      });
    }
  }

  for (const fileDiff of diffs) {
    const fileExtension = fileDiff.file.substring(
      fileDiff.file.lastIndexOf(".")
    );
    const applicableRules = allRules.filter((rule) => {
      if (!rule.fileExtensions) {
        return true;
      }
      return rule.fileExtensions.includes(fileExtension);
    });

    for (const addedLine of fileDiff.added) {
      for (const rule of applicableRules) {
        if (!rule.pattern.test(addedLine.content)) {
          continue;
        }
        reviews.push({
          comment: rule.description,
          file: fileDiff.file,
          line: addedLine.lineNumber,
          severity: rule.severity,
        });
      }
    }
  }

  return { reviews };
}
