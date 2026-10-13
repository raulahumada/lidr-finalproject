"use server";

import { redirect } from "next/navigation";

import { hashPassword } from "@/lib/auth/password";
import { prisma } from "@/lib/auth/prisma";

export type RegisterState = { error?: string };

const MIN_PASSWORD = 12;

export async function register(
  _prev: RegisterState,
  formData: FormData,
): Promise<RegisterState> {
  const email = String(formData.get("email") ?? "")
    .trim()
    .toLowerCase();
  const name = String(formData.get("name") ?? "").trim();
  const password = String(formData.get("password") ?? "");

  if (!email.includes("@")) return { error: "Ese email no parece un email." };
  if (password.length < MIN_PASSWORD) {
    return {
      error: `La contraseña tiene que tener al menos ${MIN_PASSWORD} caracteres.`,
    };
  }

  const passwordHash = await hashPassword(password);

  try {
    await prisma.user.create({
      data: {
        email,
        name: name || null,
        passwordHash,
        disabledAt: new Date(),
      },
    });
  } catch (error) {
    const code = (error as { code?: unknown } | null)?.code;
    if (code !== "P2002") throw error;
  }

  redirect("/register/pending");
}
