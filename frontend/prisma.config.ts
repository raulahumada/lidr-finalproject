import { config } from "dotenv";
import { defineConfig } from "prisma/config";

config({ path: ".env.local", quiet: true });
config({ quiet: true });

/**
 * Prisma CLI datasource for identity migrations.
 * Uses AUTH_DATABASE_URL (never the corpus DATABASE_URL).
 */
export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: {
    path: "prisma/migrations",
  },
  datasource: {
    url:
      process.env["AUTH_DATABASE_DIRECT_URL"] ?? process.env["AUTH_DATABASE_URL"],
  },
});
