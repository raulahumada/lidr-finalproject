export const CONSOLE_USER_HEADER = "X-Console-User";

const MAX_ID_CHARS = 64;

export function consoleUserHeaderFor(
  userId: string | null | undefined,
): Record<string, string> {
  const trimmed = userId?.trim();
  if (!trimmed || trimmed.length > MAX_ID_CHARS) return {};
  return { [CONSOLE_USER_HEADER]: trimmed };
}
