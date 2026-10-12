"use client";

import { useState, useTransition } from "react";

import { Banner } from "@astryxdesign/core/Banner";
import { Button } from "@astryxdesign/core/Button";
import { Heading } from "@astryxdesign/core/Heading";
import { Layout, LayoutContent, HStack, VStack } from "@astryxdesign/core/Layout";
import { List, ListItem } from "@astryxdesign/core/List";
import { Spinner } from "@astryxdesign/core/Spinner";
import { Text } from "@astryxdesign/core/Text";
import { TextArea } from "@astryxdesign/core/TextArea";
import { TextInput } from "@astryxdesign/core/TextInput";

import {
  AnswerApiError,
  postAnswer,
  type AnswerResponse,
} from "../lib/api/answer";

type UiState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: AnswerResponse }
  | { status: "error"; message: string; kind: AnswerApiError["kind"] };

function parseOptionalK(raw: string): number | undefined {
  const trimmed = raw.trim();
  if (!trimmed) return undefined;
  const n = Number(trimmed);
  if (!Number.isInteger(n) || n < 1 || n > 50) {
    throw new Error("k debe ser un entero entre 1 y 50");
  }
  return n;
}

export default function AnswerPage() {
  const [question, setQuestion] = useState("");
  const [kInput, setKInput] = useState("");
  const [ui, setUi] = useState<UiState>({ status: "idle" });
  const [isPending, startTransition] = useTransition();

  const isLoading = ui.status === "loading" || isPending;
  const canSubmit = question.trim().length > 0 && !isLoading;

  const submit = () => {
    if (!canSubmit) return;

    let k: number | undefined;
    try {
      k = parseOptionalK(kInput);
    } catch (err) {
      setUi({
        status: "error",
        message: err instanceof Error ? err.message : "k inválido",
        kind: "http",
      });
      return;
    }

    setUi({ status: "loading" });
    startTransition(async () => {
      try {
        const data = await postAnswer({
          question: question.trim(),
          ...(k !== undefined ? { k } : {}),
        });
        setUi({ status: "success", data });
      } catch (err) {
        if (err instanceof AnswerApiError) {
          setUi({
            status: "error",
            message: err.message,
            kind: err.kind,
          });
          return;
        }
        setUi({
          status: "error",
          message: "Error inesperado al pedir la respuesta",
          kind: "network",
        });
      }
    });
  };

  return (
    <Layout
      height="fill"
      contentWidth={720}
      padding={6}
      content={
        <LayoutContent>
          <VStack gap={6}>
            <VStack gap={2}>
              <Heading level={1} type="display-3">
                Respuesta
              </Heading>
              <Text type="large" color="secondary" textWrap="balance">
                Preguntá sobre el corpus Metropol Fintech. La API sync
                (POST /answer) devuelve texto grounded y citas.
              </Text>
            </VStack>

            <VStack gap={4}>
              <TextArea
                label="Pregunta"
                value={question}
                onChange={setQuestion}
                isRequired
                isDisabled={isLoading}
                placeholder="¿Cómo es el handoff de cobranzas con Tenela?"
                description="Una pregunta a la vez (chat sync, sin historial)."
              />
              <TextInput
                label="k (opcional)"
                value={kInput}
                onChange={setKInput}
                isOptional
                isDisabled={isLoading}
                description="Profundidad de retrieval (1–50). Vacío = default del backend."
                placeholder="5"
                onEnter={submit}
              />
              <HStack gap={3}>
                <Button
                  label="Preguntar"
                  variant="primary"
                  isDisabled={!canSubmit}
                  isLoading={isLoading}
                  onClick={submit}
                />
              </HStack>
            </VStack>

            {isLoading ? (
              <Spinner label="Generando respuesta…" size="lg" />
            ) : null}

            {ui.status === "error" ? (
              <Banner
                status="error"
                title={
                  ui.kind === "unavailable"
                    ? "Servicio no disponible"
                    : "No se pudo obtener la respuesta"
                }
                description={ui.message}
              />
            ) : null}

            {ui.status === "success" ? (
              <VStack gap={4}>
                {ui.data.no_evidence ? (
                  <Banner
                    status="warning"
                    title="Sin evidencia suficiente"
                    description="El corpus no devolvió chunks útiles para esta pregunta."
                  />
                ) : null}
                <VStack gap={2}>
                  <Heading level={2}>Respuesta</Heading>
                  <Text type="body" textWrap="pretty">
                    {ui.data.answer}
                  </Text>
                  <Text type="supporting" color="secondary">
                    prompt {ui.data.prompt_version} · k={ui.data.k} ·{" "}
                    {ui.data.latency_ms} ms · cached={ui.data.cached}
                  </Text>
                </VStack>
                {ui.data.citations.length > 0 ? (
                  <List
                    header={<Heading level={3}>Citas</Heading>}
                    hasDividers
                    density="compact"
                  >
                    {ui.data.citations.map((c) => (
                      <ListItem
                        key={`${c.document_id}-${c.chunk_id}`}
                        label={c.source_path}
                        description={c.excerpt}
                      />
                    ))}
                  </List>
                ) : null}
              </VStack>
            ) : null}
          </VStack>
        </LayoutContent>
      }
    />
  );
}
