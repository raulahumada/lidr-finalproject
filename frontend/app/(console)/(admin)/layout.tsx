import { redirect } from "next/navigation";

import { auth } from "@/auth";
import { asRole } from "@/lib/auth/roles";

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();
  if (!session?.user?.id) redirect("/login");
  if (asRole(session.user.role) !== "administrador") {
    redirect("/?forbidden=1");
  }
  return children;
}
