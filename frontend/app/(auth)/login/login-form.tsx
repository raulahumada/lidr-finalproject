"use client";

import { useActionState, useState, type CSSProperties } from "react";
import { Box } from "lucide-react";

import { Button } from "@astryxdesign/core/Button";
import { Card } from "@astryxdesign/core/Card";
import { Center } from "@astryxdesign/core/Center";
import { Icon } from "@astryxdesign/core/Icon";
import { VStack } from "@astryxdesign/core/Layout";
import { Link } from "@astryxdesign/core/Link";
import { Heading } from "@astryxdesign/core/Heading";
import { Text } from "@astryxdesign/core/Text";
import { TextInput } from "@astryxdesign/core/TextInput";

import { signInWithPassword, type LoginState } from "./actions";

const INITIAL: LoginState = {};

// Cap the column at 400px (Stack has no maxWidth — same as login-card template).
const contentStyle: CSSProperties = {
  width: "100%",
  maxWidth: 400,
};

export function LoginForm({
  next,
  errorMessage,
}: {
  next: string;
  errorMessage?: string;
}) {
  const [state, action, pending] = useActionState(signInWithPassword, INITIAL);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const fieldError = state.error ?? errorMessage;
  const loginFailed = Boolean(fieldError);

  return (
    <Center axis="both" padding={6}>
      <VStack gap={4} hAlign="center" style={contentStyle}>
        <VStack gap={2} hAlign="center">
          <Icon icon={Box} size="lg" />
          <Text type="body" weight="bold" size="lg">
            Entrega LiDR
          </Text>
        </VStack>

        <Card padding={8} width="100%">
          <VStack gap={4} hAlign="stretch">
            <VStack gap={1} hAlign="center">
              <Heading level={2}>Bienvenido</Heading>
              <Text type="body" color="secondary" size="sm">
                Entrá a la consola Metropol
              </Text>
            </VStack>

            <form action={action}>
              <VStack gap={4} hAlign="stretch">
                <input type="hidden" name="next" value={next} />
                <VStack gap={2}>
                  <TextInput
                    htmlName="email"
                    label="Email"
                    isLabelHidden
                    type="email"
                    placeholder="nombre@empresa.com"
                    value={email}
                    onChange={setEmail}
                    size="lg"
                    width="100%"
                  />
                  <TextInput
                    htmlName="password"
                    label="Contraseña"
                    isLabelHidden
                    placeholder="Tu contraseña"
                    type="password"
                    value={password}
                    onChange={setPassword}
                    size="lg"
                    width="100%"
                    status={
                      loginFailed
                        ? {
                            type: "error",
                            message: fieldError,
                          }
                        : undefined
                    }
                  />
                </VStack>

                <Button
                  type="submit"
                  label={pending ? "Entrando…" : "Entrar"}
                  variant="primary"
                  size="lg"
                  isLoading={pending}
                  width="100%"
                />
              </VStack>
            </form>

            <VStack hAlign="center">
              <Text type="supporting" color="secondary">
                ¿No tenés cuenta?{" "}
                <Link href="/register" type="supporting">
                  Registrate
                </Link>
              </Text>
            </VStack>
          </VStack>
        </Card>

        <VStack hAlign="center" width="100%">
          <Text type="supporting" color="secondary" justify="center">
            Las cuentas nuevas quedan pendientes hasta que un administrador las
            habilite.
          </Text>
        </VStack>
      </VStack>
    </Center>
  );
}
