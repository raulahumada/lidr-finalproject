import { Heading } from "@astryxdesign/core/Heading";
import {
  Layout,
  LayoutContent,
  VStack,
} from "@astryxdesign/core/Layout";
import { Text } from "@astryxdesign/core/Text";

import { auth } from "@/auth";
import { prisma } from "@/lib/auth/prisma";

import { UsersConsole, type AccountRow } from "./users-console";

export const metadata = {
  title: "Usuarios · Entrega LiDR",
};

export default async function UsersPage() {
  const session = await auth();

  const rows = await prisma.user.findMany({
    select: {
      id: true,
      name: true,
      email: true,
      role: true,
      disabledAt: true,
      passwordHash: true,
      createdAt: true,
      accounts: { select: { provider: true } },
    },
    orderBy: [{ disabledAt: "desc" }, { createdAt: "asc" }],
  });

  const accounts: AccountRow[] = rows.map((row) => ({
    id: row.id,
    name: row.name,
    email: row.email,
    role: row.role,
    enabled: row.disabledAt === null,
    createdAt: row.createdAt.toISOString(),
    hasPassword: Boolean(row.passwordHash),
    hasGoogle: row.accounts.some((account) => account.provider === "google"),
  }));

  return (
    <Layout>
      <LayoutContent padding={6}>
        <VStack gap={5}>
          <VStack gap={2}>
            <Heading level={1}>Usuarios</Heading>
            <Text color="secondary">
              Cualquiera puede registrarse; nadie entra hasta que alguien de acá
              lo habilite.
            </Text>
          </VStack>
          <UsersConsole
            accounts={accounts}
            currentUserId={session?.user?.id ?? ""}
          />
        </VStack>
      </LayoutContent>
    </Layout>
  );
}
