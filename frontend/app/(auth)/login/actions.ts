"use server";

import { AuthError } from "next-auth";

import { signIn } from "@/auth";
import { safeRedirect } from "@/lib/auth/safe-redirect";

export type LoginState = { error?: string };

const GENERIC_FAILURE = "Email o contraseña incorrectos.";

export async function signInWithPassword(
  _prev: LoginState,
  formData: FormData,
): Promise<LoginState> {
  const email = String(formData.get("email") ?? "");
  const password = String(formData.get("password") ?? "");
  const next = safeRedirect(String(formData.get("next") ?? ""));

  if (!email || !password) {
    return { error: "Completá email y contraseña." };
  }

  try {
    await signIn("credentials", { email, password, redirectTo: next });
  } catch (error) {
    if (error instanceof AuthError) return { error: GENERIC_FAILURE };
    throw error;
  }

  return {};
}
