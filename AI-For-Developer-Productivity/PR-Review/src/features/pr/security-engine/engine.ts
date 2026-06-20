import type { ParsedFileDiff } from "@src/features/pr/git-diff";
import {
  type Findings,
  rules as defaultRules,
  type SecurityRule,
} from "@src/features/pr/security-engine";
import { getConfig } from "@src/shared";

export function runSecurityEngine(diffs: ParsedFileDiff[]): Findings[] {
  const findings: Findings[] = [];
  const config = getConfig();
  const rules: SecurityRule[] = [...defaultRules];

  if (config.rules) {
    for (const rule of config.rules) {
      rules.push({
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
    const applicableRules = rules.filter((rule) => {
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
        findings.push({
          description: rule.description,
          file: fileDiff.file,
          line: addedLine.lineNumber,
          severity: rule.severity,
        });
      }
    }
  }

  return findings;
}
