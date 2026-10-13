import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { auth } from "@/auth";
import { safeRedirect } from "@/lib/auth/safe-redirect";

import { LoginForm } from "./login-form";

export const metadata: Metadata = {
  title: "Entrar · Entrega LiDR",
};

const ERROR_MESSAGES: Record<string, string> = {
  AccountDisabled:
    "Tu cuenta todavía no está habilitada. Un administrador tiene que hacerlo antes de que puedas entrar.",
  AccessDenied: "No se pudo entrar con esa cuenta.",
  Verification: "El enlace venció o ya se usó. Probá entrar de nuevo.",
};

const UNKNOWN_ERROR = "No se pudo entrar. Probá de nuevo.";

export default async function LoginPage(props: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const searchParams = await props.searchParams;
  const next = safeRedirect(searchParams.next);

  const session = await auth();
  if (session?.user?.id) redirect(next);

  const rawError = searchParams.error;
  const errorCode = typeof rawError === "string" ? rawError : undefined;
  const errorMessage = errorCode
    ? (ERROR_MESSAGES[errorCode] ?? UNKNOWN_ERROR)
    : undefined;

  return <LoginForm next={next} errorMessage={errorMessage} />;
}
