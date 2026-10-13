import { PrismaPg } from "@prisma/adapter-pg";
import { Pool } from "pg";

import { PrismaClient } from "@/lib/generated/prisma/client";

function createClient(): PrismaClient {
  const connectionString = process.env.AUTH_DATABASE_URL;
  if (!connectionString) {
    throw new Error(
      "Falta AUTH_DATABASE_URL. Es la base de identidad, NO la del corpus " +
        "(DATABASE_URL del backend).",
    );
  }

  const pool = new Pool({
    connectionString,
    max: Number(process.env.AUTH_DATABASE_POOL_MAX ?? 5),
    idleTimeoutMillis: 10_000,
  });

  return new PrismaClient({ adapter: new PrismaPg(pool) });
}

const globalForPrisma = globalThis as unknown as {
  authPrisma?: PrismaClient;
};

export const prisma: PrismaClient = globalForPrisma.authPrisma ?? createClient();

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.authPrisma = prisma;
}
