import type { Role } from "@/lib/auth/roles";

export type Refusal = string | null;

export type TargetAccount = {
  id: string;
  role: Role;
  disabledAt: Date | null;
};

export function refuseRoleChange(
  actorId: string,
  target: TargetAccount,
  nextRole: Role,
  otherEnabledAdmins: number,
): Refusal {
  if (actorId === target.id) {
    return "No podés cambiar tu propio rol. Pedíselo a otro administrador.";
  }
  if (target.role === nextRole) return null;
  return refuseIfLastAdmin(target, otherEnabledAdmins, "degradar");
}

export function refuseDisable(
  target: TargetAccount,
  otherEnabledAdmins: number,
): Refusal {
  if (target.disabledAt) return null;
  return refuseIfLastAdmin(target, otherEnabledAdmins, "deshabilitar");
}

export function refuseDelete(
  actorId: string,
  target: TargetAccount,
  otherEnabledAdmins: number,
): Refusal {
  if (actorId === target.id) {
    return "No podés borrar tu propia cuenta. Pedíselo a otro administrador.";
  }
  return refuseIfLastAdmin(target, otherEnabledAdmins, "borrar");
}

function refuseIfLastAdmin(
  target: TargetAccount,
  otherEnabledAdmins: number,
  verb: string,
): Refusal {
  const targetIsEnabledAdmin =
    target.role === "administrador" && target.disabledAt === null;
  if (!targetIsEnabledAdmin) return null;
  if (otherEnabledAdmins > 0) return null;
  return (
    `No se puede ${verb} al último administrador habilitado: la consola ` +
    "quedaría sin nadie que pueda configurarla."
  );
}
