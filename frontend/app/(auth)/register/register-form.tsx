"use client";

import { useActionState, useState } from "react";
import Link from "next/link";

import { Banner } from "@astryxdesign/core/Banner";
import { Button } from "@astryxdesign/core/Button";
import { Heading } from "@astryxdesign/core/Heading";
import { HStack, VStack } from "@astryxdesign/core/Layout";
import { TextInput } from "@astryxdesign/core/TextInput";
import { Text } from "@astryxdesign/core/Text";

import { register, type RegisterState } from "./actions";

const INITIAL: RegisterState = {};

export function RegisterForm() {
  const [state, action, pending] = useActionState(register, INITIAL);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  return (
    <VStack gap={5} width="100%">
      <VStack gap={2}>
        <Heading level={1}>Crear cuenta</Heading>
        <Text color="secondary">
          La cuenta queda pendiente hasta que un administrador la habilite.
        </Text>
      </VStack>

      {state.error ? (
        <Banner status="error" title="Error" description={state.error} />
      ) : null}

      <form action={action}>
        <VStack gap={4}>
          <TextInput
            htmlName="name"
            label="Nombre"
            value={name}
            onChange={setName}
            width="100%"
          />
          <TextInput
            htmlName="email"
            type="email"
            label="Email"
            value={email}
            onChange={setEmail}
            isRequired
            width="100%"
          />
          <TextInput
            htmlName="password"
            type="password"
            label="Contraseña (mín. 12)"
            value={password}
            onChange={setPassword}
            isRequired
            width="100%"
          />
          <Button
            type="submit"
            variant="primary"
            label={pending ? "Creando…" : "Registrarme"}
            isDisabled={pending}
            width="100%"
          />
        </VStack>
      </form>

      <HStack gap={2} justify="center">
        <Text color="secondary">¿Ya tenés cuenta?</Text>
        <Link href="/login">Entrar</Link>
      </HStack>
    </VStack>
  );
}
