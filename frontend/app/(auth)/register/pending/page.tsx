import Link from "next/link";

import { Heading } from "@astryxdesign/core/Heading";
import { VStack } from "@astryxdesign/core/Layout";
import { Text } from "@astryxdesign/core/Text";

export default function RegisterPendingPage() {
  return (
    <VStack gap={4}>
      <Heading level={1}>Cuenta creada</Heading>
      <Text>
        Tu cuenta quedó pendiente de habilitación. Cuando un administrador te
        habilite, vas a poder entrar desde el login.
      </Text>
      <Link href="/login">Ir a entrar</Link>
    </VStack>
  );
}
