import { Button } from "@astryxdesign/core/Button";
import { Heading } from "@astryxdesign/core/Heading";
import { HStack, VStack } from "@astryxdesign/core/Layout";
import { Text } from "@astryxdesign/core/Text";

export default function Home() {
  return (
    <VStack gap={6}>
      <VStack gap={3}>
        <Heading level={1} type="display-3">
          Inicio
        </Heading>
        <Text type="large" color="secondary" textWrap="balance">
          Shell con sidebar Astryx. El contenido de cada ruta vive acá adentro.
        </Text>
      </VStack>
      <HStack gap={3}>
        <Button
          label="API docs"
          variant="primary"
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
        />
        <Button
          label="Astryx docs"
          variant="secondary"
          href="https://astryx.dev"
          target="_blank"
          rel="noopener noreferrer"
        />
      </HStack>
    </VStack>
  );
}
