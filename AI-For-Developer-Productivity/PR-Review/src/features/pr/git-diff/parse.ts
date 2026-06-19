import type {
  Change,
  DiffLine,
  ParsedFileDiff,
} from "@src/features/pr/git-diff";
import { getConfig } from "@src/shared";
import { minimatch } from "minimatch";
import parseDiff from "parse-diff";

const DEFAULT_IGNORED_PATTERNS = [
  "*.png",
  "*.jpg",
  "*.jpeg",
  "*.gif",
  "*.svg",
  "*.ico",
  "*.pdf",
  "*.mp3",
  "*.mp4",
  "*.map",
  "package-lock.json",
  "pnpm-lock.yaml",
  "bun.lockb",
  "go.sum",
  "Cargo.lock",
  "Gemfile.lock",
  "composer.lock",
];

// Parses a raw git diff string and filters out files
export function parseGitDiff(diff: string): ParsedFileDiff[] {
  const parsedFiles = parseDiff(diff);

  const config = getConfig();
  const ignoredPatterns = [
    ...DEFAULT_IGNORED_PATTERNS,
    ...(config.ignore || []),
  ];
  const scanPatterns = config.filesToScan || [];

  return parsedFiles
    .map((file) => {
      const fileName = file.to ?? file.from ?? "unknown";

      // Check if it should be included in scan patterns
      if (scanPatterns.length > 0) {
        const matchesScan = scanPatterns.some((p) => minimatch(fileName, p));
        if (!matchesScan) {
          return null;
        }
      }

      // Check if it should be explicitly ignored
      const isIgnored = ignoredPatterns.some((p) =>
        minimatch(fileName, p, { matchBase: true })
      );
      if (isIgnored) {
        return null;
      }

      // Process changes only for files that passed the filters
      const added: Change[] = [];
      const removed: Change[] = [];
      const context: Change[] = [];
      const changesList: DiffLine[] = [];

      for (const chunk of file.chunks) {
        for (const change of chunk.changes) {
          const content = change.content.slice(1);
          switch (change.type) {
            case "add":
              added.push({ content, lineNumber: change.ln });
              changesList.push({ content, lineNumber: change.ln, prefix: "+" });
              break;
            case "del":
              removed.push({ content, lineNumber: change.ln });
              changesList.push({ content, lineNumber: change.ln, prefix: "-" });
              break;
            case "normal":
              context.push({ content, lineNumber: change.ln2 });
              changesList.push({
                content,
                lineNumber: change.ln2,
                prefix: " ",
              });
              break;
          }
        }
      }

      return {
        added,
        changes: changesList,
        context,
        file: fileName,
        removed,
      };
    })
    .filter((file): file is ParsedFileDiff => file !== null); // Filter out null values from ignored/skipped files
}
