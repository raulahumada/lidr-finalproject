import type { Session } from "next-auth";

import { auth } from "@/auth";
import { mayCallAdminRoute } from "@/lib/auth/roles";

/** null if caller may proceed; otherwise a Response to return as-is. */
export async function requireSession(): Promise<
  { session: Session } | Response
> {
  const session = await auth();
  if (!session?.user?.id) {
    return Response.json(
      { error: "Tenés que iniciar sesión.", status: 401 },
      { status: 401 },
    );
  }
  return { session };
}

export async function requireAdmin(): Promise<Response | null> {
  const session = await auth();
  if (!session?.user || !mayCallAdminRoute(session.user.role)) {
    return Response.json(
      {
        error: "Solo un administrador puede ver esto.",
        status: 403,
      },
      { status: 403 },
    );
  }
  return null;
}
