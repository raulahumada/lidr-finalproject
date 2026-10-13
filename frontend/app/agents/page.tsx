"use client";

import { useEffect, useState } from "react";

import { Banner } from "@astryxdesign/core/Banner";
import { Heading } from "@astryxdesign/core/Heading";
import { HStack, VStack } from "@astryxdesign/core/Layout";
import { List, ListItem } from "@astryxdesign/core/List";
import { Text } from "@astryxdesign/core/Text";

import { AnswerApiError } from "../lib/api/answer";
import {
  fetchAgentCatalog,
  type AgentCatalogResponse,
} from "../lib/api/agents";

export default function AgentsPage() {
  const [catalog, setCatalog] = useState<AgentCatalogResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const data = await fetchAgentCatalog();
        if (!cancelled) {
          setCatalog(data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof AnswerApiError
              ? err.message
              : err instanceof Error
                ? err.message
                : "No se pudo cargar el catálogo",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <VStack gap={6}>
      <VStack gap={2}>
        <Heading level={1}>Agentes</Heading>
        <Text color="secondary">
          Catálogo del grafo agentic Metropol (orquestador + especialistas) y
          knobs efectivos del servicio.
        </Text>
      </VStack>

      {error ? (
        <Banner status="error" title="Catálogo" description={error} />
      ) : null}

      {loading && !catalog ? (
        <Text type="body" color="secondary">
          Cargando catálogo…
        </Text>
      ) : null}

      {catalog ? (
        <>
          <List
            header={<Heading level={2}>Roles</Heading>}
            hasDividers
            density="compact"
          >
            {catalog.agents.map((agent) => (
              <ListItem
                key={agent.key}
                label={agent.label}
                description={`${agent.role}${
                  agent.llm_driven ? " · LLM" : ""
                }${
                  agent.tools.length > 0
                    ? ` · tools: ${agent.tools.join(", ")}`
                    : ""
                }`}
              />
            ))}
          </List>

          <VStack gap={3}>
            <Heading level={2}>Escalera</Heading>
            <Text type="supporting" color="secondary">
              {catalog.ladder.join(" → ")}
            </Text>
          </VStack>

          <VStack gap={3}>
            <Heading level={2}>Dominios</Heading>
            <HStack gap={2} wrap="wrap">
              {catalog.domains.map((domain) => (
                <Text key={domain} type="supporting">
                  {domain}
                </Text>
              ))}
            </HStack>
          </VStack>

          <List
            header={<Heading level={2}>Knobs</Heading>}
            hasDividers
            density="compact"
          >
            <ListItem
              label="agentic_orchestrator_max_steps"
              description={String(catalog.knobs.agentic_orchestrator_max_steps)}
            />
            <ListItem
              label="agentic_confidence_threshold"
              description={String(
                catalog.knobs.agentic_confidence_threshold,
              )}
            />
          </List>
        </>
      ) : null}
    </VStack>
  );
}
