import { createInterface } from "node:readline/promises";
import { stdin, stdout } from "node:process";

import "./load-env";

import { hashPassword } from "../lib/auth/password";
import { prisma } from "../lib/auth/prisma-client";

/**
 * Creates or promotes the first administrator.
 *
 *   npm run seed:admin -- ada@example.com
 *
 * Password from AUTH_SEED_PASSWORD env, or prompted on the terminal.
 */

async function main(): Promise<void> {
  const email = process.argv[2]?.trim().toLowerCase();
  if (!email || !email.includes("@")) {
    console.error("Uso: npm run seed:admin -- <email>");
    process.exitCode = 1;
    return;
  }

  let password = process.env.AUTH_SEED_PASSWORD?.trim() ?? "";
  if (!password) {
    const rl = createInterface({ input: stdin, output: stdout });
    password = (
      await rl.question(`Contraseña para ${email} (se va a ver): `)
    ).trim();
    rl.close();
  }

  if (password.length < 12) {
    console.error("La contraseña tiene que tener al menos 12 caracteres.");
    process.exitCode = 1;
    return;
  }

  const passwordHash = await hashPassword(password);

  const user = await prisma.user.upsert({
    where: { email },
    update: {
      passwordHash,
      role: "administrador",
      disabledAt: null,
    },
    create: {
      email,
      passwordHash,
      role: "administrador",
      disabledAt: null,
    },
  });

  console.log(`Listo: ${user.email} es administrador (id ${user.id}).`);
}

main()
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(() => prisma.$disconnect());
