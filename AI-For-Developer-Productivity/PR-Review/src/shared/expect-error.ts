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
