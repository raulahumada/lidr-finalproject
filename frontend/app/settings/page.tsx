import { Heading } from "@astryxdesign/core/Heading";
import { VStack } from "@astryxdesign/core/Layout";
import { Text } from "@astryxdesign/core/Text";

export default function SettingsPage() {
  return (
    <VStack gap={3}>
      <Heading level={1}>Ajustes</Heading>
      <Text color="secondary">Placeholder de configuración.</Text>
    </VStack>
  );
}
