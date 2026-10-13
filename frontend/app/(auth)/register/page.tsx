import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { auth } from "@/auth";

import { RegisterForm } from "./register-form";

export const metadata: Metadata = {
  title: "Registro · Entrega LiDR",
};

export default async function RegisterPage() {
  const session = await auth();
  if (session?.user?.id) redirect("/");

  return <RegisterForm />;
}
