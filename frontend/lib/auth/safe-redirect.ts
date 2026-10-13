export const DEFAULT_REDIRECT = "/";

export function safeRedirect(next: string | string[] | undefined): string {
  if (typeof next !== "string") return DEFAULT_REDIRECT;
  if (!next.startsWith("/")) return DEFAULT_REDIRECT;
  if (next.startsWith("//") || next.startsWith("/\\")) return DEFAULT_REDIRECT;
  if (next === "/login" || next.startsWith("/login?")) return DEFAULT_REDIRECT;
  return next;
}
