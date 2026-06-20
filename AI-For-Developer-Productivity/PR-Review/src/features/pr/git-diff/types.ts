export type Change = {
  content: string;
  lineNumber: number;
};

export type DiffLine = {
  content: string;
  lineNumber: number;
  prefix: string;
};

export type ParsedFileDiff = {
  added: Change[];
  changes: DiffLine[];
  context: Change[];
  file: string;
  removed: Change[];
};
