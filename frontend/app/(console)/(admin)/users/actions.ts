"use server";

import { revalidatePath } from "next/cache";

import { auth } from "@/auth";
import {
  refuseDelete,
  refuseDisable,
  refuseRoleChange,
  type TargetAccount,
} from "@/lib/auth/guards";
import { prisma } from "@/lib/auth/prisma";
import { asRole, type Role } from "@/lib/auth/roles";

export type ActionResult = { error?: string };

const NOT_ALLOWED = "No tenés permiso para esto.";
const GONE = "Esa cuenta ya no existe.";

async function requireAdmin(): Promise<{ id: string } | { error: string }> {
  const session = await auth();
  if (!session?.user?.id) return { error: NOT_ALLOWED };
  if (asRole(session.user.role) !== "administrador") {
    return { error: NOT_ALLOWED };
  }
  return { id: session.user.id };
}

async function loadTarget(
  tx: Pick<typeof prisma, "user">,
  id: string,
): Promise<{ target: TargetAccount; otherEnabledAdmins: number } | null> {
  const target = await tx.user.findUnique({
    where: { id },
    select: { id: true, role: true, disabledAt: true },
  });
  if (!target) return null;

  const otherEnabledAdmins = await tx.user.count({
    where: { role: "administrador", disabledAt: null, id: { not: id } },
  });
  return { target, otherEnabledAdmins };
}

export async function setRole(
  userId: string,
  nextRole: Role,
): Promise<ActionResult> {
  const actor = await requireAdmin();
  if ("error" in actor) return actor;

  const result = await prisma.$transaction(async (tx) => {
    const loaded = await loadTarget(tx, userId);
    if (!loaded) return { error: GONE };

    const refusal = refuseRoleChange(
      actor.id,
      loaded.target,
      nextRole,
      loaded.otherEnabledAdmins,
    );
    if (refusal) return { error: refusal };

    await tx.user.update({ where: { id: userId }, data: { role: nextRole } });
    return {};
  });

  revalidatePath("/users");
  return result;
}

export async function setEnabled(
  userId: string,
  enabled: boolean,
): Promise<ActionResult> {
  const actor = await requireAdmin();
  if ("error" in actor) return actor;

  const result = await prisma.$transaction(async (tx) => {
    const loaded = await loadTarget(tx, userId);
    if (!loaded) return { error: GONE };

    if (!enabled) {
      const refusal = refuseDisable(loaded.target, loaded.otherEnabledAdmins);
      if (refusal) return { error: refusal };
    }

    await tx.user.update({
      where: { id: userId },
      data: { disabledAt: enabled ? null : new Date() },
    });
    return {};
  });

  revalidatePath("/users");
  return result;
}

export async function deleteUser(userId: string): Promise<ActionResult> {
  const actor = await requireAdmin();
  if ("error" in actor) return actor;

  const result = await prisma.$transaction(async (tx) => {
    const loaded = await loadTarget(tx, userId);
    if (!loaded) return { error: GONE };

    const refusal = refuseDelete(
      actor.id,
      loaded.target,
      loaded.otherEnabledAdmins,
    );
    if (refusal) return { error: refusal };

    await tx.user.delete({ where: { id: userId } });
    return {};
  });

  revalidatePath("/users");
  return result;
}
