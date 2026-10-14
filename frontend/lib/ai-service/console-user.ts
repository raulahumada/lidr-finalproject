/**
 * Build the X-Console-User header value from the Auth.js session user id.
 * Backend SessionStore uses it for transcript ownership scoping.
 *
 * || Arma X-Console-User desde el user id de Auth.js (ownership de sesiones).
 */

export const CONSOLE_USER_HEADER = "X-Console-User";

const MAX_ID_CHARS = 64;

export function consoleUserHeaderFor(
  userId: string | null | undefined,
): Record<string, string> {
  const trimmed = userId?.trim();
  if (!trimmed || trimmed.length > MAX_ID_CHARS) return {};
  return { [CONSOLE_USER_HEADER]: trimmed };
}
