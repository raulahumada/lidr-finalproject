"use client";

import { useState, useTransition } from "react";

import { Banner } from "@astryxdesign/core/Banner";
import { Button } from "@astryxdesign/core/Button";
import { HStack, VStack } from "@astryxdesign/core/Layout";
import { Text } from "@astryxdesign/core/Text";

import type { Role } from "@/lib/auth/roles";

import { deleteUser, setEnabled, setRole } from "./actions";

export type AccountRow = {
  id: string;
  name: string | null;
  email: string;
  role: Role;
  enabled: boolean;
  createdAt: string;
  hasPassword: boolean;
  hasGoogle: boolean;
};

export function UsersConsole({
  accounts,
  currentUserId,
}: {
  accounts: AccountRow[];
  currentUserId: string;
}) {
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function run(fn: () => Promise<{ error?: string }>) {
    setError(null);
    startTransition(async () => {
      const result = await fn();
      if (result.error) setError(result.error);
    });
  }

  return (
    <VStack gap={4}>
      {error ? (
        <Banner
          status="error"
          title="No se pudo aplicar"
          description={error}
        />
      ) : null}

      {accounts.map((row) => (
        <VStack key={row.id} gap={2}>
          <HStack gap={3} align="center" wrap="wrap">
            <Text weight="semibold">{row.email}</Text>
            {row.name ? <Text color="secondary">{row.name}</Text> : null}
            <Text color="secondary">
              {row.role} · {row.enabled ? "habilitada" : "pendiente"}
            </Text>
          </HStack>
          <HStack gap={2} wrap="wrap">
            <Button
              size="sm"
              variant="secondary"
              label="Habilitar"
              isDisabled={pending || row.enabled}
              onClick={() => run(() => setEnabled(row.id, true))}
            />
            <Button
              size="sm"
              variant="secondary"
              label="Deshabilitar"
              isDisabled={pending || !row.enabled}
              onClick={() => run(() => setEnabled(row.id, false))}
            />
            <Button
              size="sm"
              variant="secondary"
              label="Hacer admin"
              isDisabled={
                pending ||
                row.role === "administrador" ||
                row.id === currentUserId
              }
              onClick={() => run(() => setRole(row.id, "administrador"))}
            />
            <Button
              size="sm"
              variant="secondary"
              label="Hacer usuario"
              isDisabled={
                pending || row.role === "usuario" || row.id === currentUserId
              }
              onClick={() => run(() => setRole(row.id, "usuario"))}
            />
            <Button
              size="sm"
              variant="destructive"
              label="Borrar"
              isDisabled={pending || row.id === currentUserId}
              onClick={() => run(() => deleteUser(row.id))}
            />
          </HStack>
        </VStack>
      ))}
    </VStack>
  );
}
