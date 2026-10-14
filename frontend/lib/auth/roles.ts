/**
 * Console roles and admin-only path / upstream-route guards.
 *
 * Registration creates `usuario` (often disabled until an admin enables the
 * account). Admin screens and admin FastAPI prefixes are gated here.
 *
 * || Roles de consola y guards de rutas admin (UI + upstream).
 */
export const ROLES = ["usuario", "administrador"] as const;
export type Role = (typeof ROLES)[number];

export const DEFAULT_ROLE: Role = "usuario";

/** Screens that require administrador (prefix match). */
const ADMIN_ONLY = [
  "/agents",
  "/settings",
  "/ingest",
  "/users",
  "/usage",
] as const;

export function isAdminOnly(pathname: string): boolean {
  return ADMIN_ONLY.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

export function canAccess(role: Role | undefined, pathname: string): boolean {
  if (!isAdminOnly(pathname)) return true;
  return role === "administrador";
}

export function asRole(value: unknown): Role {
  return ROLES.includes(value as Role) ? (value as Role) : DEFAULT_ROLE;
}

export function mayCallAdminRoute(role: unknown): boolean {
  return asRole(role) === "administrador";
}

/** FastAPI path prefixes that require administrador on the BFF. */
export function isAdminUpstreamPath(pathname: string): boolean {
  if (pathname.startsWith("/api/v1/config")) return true;
  if (pathname.startsWith("/api/v1/ingest")) return true;
  if (pathname.startsWith("/api/v1/answer/agents")) return true;
  if (pathname.startsWith("/api/v1/usage")) return true;
  return false;
}
