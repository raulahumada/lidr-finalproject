import { Badge } from "@astryxdesign/core/Badge";
import { Button } from "@astryxdesign/core/Button";
import { Heading } from "@astryxdesign/core/Heading";
import {
  HStack,
  Layout,
  LayoutContent,
  VStack,
} from "@astryxdesign/core/Layout";
import { Text } from "@astryxdesign/core/Text";

export default function Home() {
  return (
    <Layout
      height="fill"
      padding={0}
      content={
        <LayoutContent padding={6} isScrollable>
          <VStack gap={8} justify="center" height="100%">
            <VStack gap={4} maxWidth={720}>
              <HStack gap={2} wrap="wrap" align="center">
                <Badge variant="teal" label="Entrega LiDR" />
                <Badge variant="neutral" label="Metropol Fintech" />
              </HStack>
              <Heading level={1} type="display-3">
                Consola Metropol
              </Heading>
              <Text type="large" color="secondary" textWrap="balance">
                Plataforma multiagente + RAG sobre la documentación de
                omnicanalidad, ventas, cobranzas y Tenela. Preguntá con
                evidencia citada, inspeccioná el retrieve o afiná los agentes
                del grafo.
              </Text>
            </VStack>

            <HStack gap={3} wrap="wrap">
              <Button label="Abrir chat" variant="primary" href="/answer" />
              <Button
                label="Agentes"
                variant="secondary"
                href="/agents"
              />
              <Button label="Búsqueda" variant="ghost" href="/search" />
            </HStack>

            <Text type="supporting" color="secondary">
              Chat = respuesta grounded · Búsqueda = hits del corpus · Agentes =
              ladder y customs
            </Text>
          </VStack>
        </LayoutContent>
      }
    />
  );
}
