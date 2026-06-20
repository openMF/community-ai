import * as core from "@actions/core";

export async function expectError<T, E extends new (message?: string) => Error>(
  promise: Promise<T>,
  errorsToCatch?: E[]
): Promise<[undefined, T] | [InstanceType<E>]> {
  return promise
    .then((data) => {
      return [undefined, data] as [undefined, T];
    })
    .catch((error) => {
      if (errorsToCatch === undefined) {
        return [error];
      }
      if (errorsToCatch.some((e) => error instanceof e)) {
        return [error];
      }
      throw error;
    });
}

export function failAction(contextMessage: string, error: unknown): void {
  let details: string;
  if (error instanceof Error) {
    details = error.message;
    if (error.cause) {
      let causeMessage: string;
      if (error.cause instanceof Error) {
        causeMessage = error.cause.message;
      } else {
        causeMessage = String(error.cause);
      }
      details += `\nCause: ${causeMessage}`;
    }
    if (error.stack) {
      core.debug(error.stack);
    }
  } else {
    details = String(error);
  }
  const message = `${contextMessage}: ${details}`;

  core.error(message);
  core.setFailed(message);
}
