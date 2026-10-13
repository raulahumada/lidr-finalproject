import { redirect } from "next/navigation";

import { auth } from "@/auth";

import { AppShellLayout } from "../components/app-shell";

export default async function ConsoleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();
  if (!session?.user?.id) {
    redirect("/login");
  }

  return (
    <AppShellLayout role={session.user.role}>{children}</AppShellLayout>
  );
}
