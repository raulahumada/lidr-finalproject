import { Heading } from "@astryxdesign/core/Heading";
import { VStack } from "@astryxdesign/core/Layout";
import { Text } from "@astryxdesign/core/Text";

export default function ItemsPage() {
  return (
    <VStack gap={3}>
      <Heading level={1}>Items</Heading>
      <Text color="secondary">
        Placeholder — acá irá el listado conectado al backend.
      </Text>
    </VStack>
  );
}
