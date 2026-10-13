import { PrismaAdapter } from "@auth/prisma-adapter";
import NextAuth from "next-auth";
import type { Adapter } from "next-auth/adapters";
import Credentials from "next-auth/providers/credentials";

import { verifyPassword } from "@/lib/auth/password";
import { prisma } from "@/lib/auth/prisma";
import { asRole, type Role } from "@/lib/auth/roles";

declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      role: Role;
      name?: string | null;
      email?: string | null;
      image?: string | null;
    };
  }
}

function identityAdapter(): Adapter {
  const adapter = PrismaAdapter(prisma);
  return {
    ...adapter,
    createUser: (data) =>
      adapter.createUser!({ ...data, disabledAt: new Date() } as typeof data),
  };
}

const DISABLED_REDIRECT = "/login?error=AccountDisabled";

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: identityAdapter(),
  // Required with Credentials: adapter would otherwise default to database sessions.
  session: { strategy: "jwt" },
  pages: {
    signIn: "/login",
    error: "/login",
  },
  // Credentials only for now; Google OAuth deferred.
  providers: [
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Contraseña", type: "password" },
      },
      async authorize(credentials) {
        const email = String(credentials?.email ?? "")
          .trim()
          .toLowerCase();
        const password = String(credentials?.password ?? "");
        if (!email || !password) return null;

        const user = await prisma.user.findUnique({ where: { email } });
        if (!user) return null;
        if (!(await verifyPassword(password, user.passwordHash))) return null;

        return {
          id: user.id,
          email: user.email,
          name: user.name,
          image: user.image,
          role: user.role,
          disabledAt: user.disabledAt,
        };
      },
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider === "credentials") {
        const disabled = (user as { disabledAt?: Date | null }).disabledAt;
        return disabled ? DISABLED_REDIRECT : true;
      }
      return true;
    },

    async jwt({ token, user }) {
      if (user) {
        token.sub = user.id;
        token.role = asRole((user as { role?: unknown }).role);
        return token;
      }

      const id = token.sub;
      if (!id) return null;

      const row = await prisma.user.findUnique({
        where: { id },
        select: { role: true, disabledAt: true },
      });
      if (!row || row.disabledAt) return null;

      token.role = asRole(row.role);
      return token;
    },

    async session({ session, token }) {
      session.user.id = String(token.sub ?? "");
      session.user.role = asRole(token.role);
      return session;
    },
  },
});
