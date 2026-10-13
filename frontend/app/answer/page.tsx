"use client";

import { useEffect, useRef, useState, useTransition } from "react";

import { Avatar } from "@astryxdesign/core/Avatar";
import { Banner } from "@astryxdesign/core/Banner";
import { Button } from "@astryxdesign/core/Button";
import {
  ChatComposer,
  ChatComposerInput,
  ChatLayout,
  ChatMessage,
  ChatMessageBubble,
  ChatMessageList,
  ChatMessageMetadata,
  ChatSystemMessage,
  ChatToolCalls,
} from "@astryxdesign/core/Chat";
import { ClickableCard } from "@astryxdesign/core/ClickableCard";
import { EmptyState } from "@astryxdesign/core/EmptyState";
import { Heading } from "@astryxdesign/core/Heading";
import { Grid } from "@astryxdesign/core/Grid";
import { HStack, Layout, LayoutContent, VStack } from "@astryxdesign/core/Layout";
import { List, ListItem } from "@astryxdesign/core/List";
import { Markdown } from "@astryxdesign/core/Markdown";
import { Text } from "@astryxdesign/core/Text";
import { TextArea } from "@astryxdesign/core/TextArea";

import { AnswerApiError } from "../lib/api/answer";
import {
  resumeAgenticAnswer,
  runAgenticWithProgress,
  type AgenticAnswerResponse,
  type GraphActivityEntry,
} from "../lib/api/agentic";

const SUGGESTIONS = [
  "¿Cómo es el handoff de cobranzas con Tenela?",
  "¿Qué canales cubre la omnicanalidad de Metropol?",
  "¿Cómo se gestiona el proceso de ventas?",
];

/** Fixed Metropol pipeline order for live step UI. */
const PIPELINE_NODES = [
  { node: "intent_framer", label: "Encuadre de intención" },
  { node: "corpus_fetcher", label: "Recuperación de evidencia" },
  { node: "grounded_composer", label: "Síntesis grounded" },
  { node: "source_guard", label: "Validación de citas" },
  { node: "escalation_gate", label: "Gate de revisión" },
] as const;

type UiState =
  | { status: "idle" }
  | { status: "loading"; question: string }
  | {
      status: "completed" | "awaiting_review" | "rejected";
      question: string;
      data: AgenticAnswerResponse;
    }
  | {
      status: "error";
      question?: string;
      message: string;
      kind: AnswerApiError["kind"];
      httpStatus: number | null;
    };

function mapAgenticUi(
  question: string,
  data: AgenticAnswerResponse,
): Exclude<UiState, { status: "idle" | "loading" | "error" }> {
  if (data.status === "awaiting_human_review") {
    return { status: "awaiting_review", question, data };
  }
  if (data.status === "rejected") {
    return { status: "rejected", question, data };
  }
  return { status: "completed", question, data };
}

function buildLiveCalls(activity: GraphActivityEntry[]) {
  const byNode = new Map<string, GraphActivityEntry>();
  for (const entry of activity) {
    byNode.set(entry.node, entry);
  }

  let sawIncomplete = false;
  return PIPELINE_NODES.map((step) => {
    const entry = byNode.get(step.node);
    if (entry) {
      return {
        key: step.node,
        name: step.node,
        target: entry.message || step.label,
        status: "complete" as const,
      };
    }
    if (!sawIncomplete) {
      sawIncomplete = true;
      return {
        key: step.node,
        name: step.node,
        target: step.label,
        status: "running" as const,
      };
    }
    return {
      key: step.node,
      name: step.node,
      target: step.label,
      status: "pending" as const,
    };
  });
}

function buildTraceCalls(data: AgenticAnswerResponse) {
  if (data.agent_trace.length === 0) return [];
  return data.agent_trace.map((step, i) => ({
    key: `${step.node}-${i}`,
    name: step.node,
    target: step.summary,
    status: "complete" as const,
  }));
}

export default function AnswerPage() {
  const [draft, setDraft] = useState("");
  const [adjustText, setAdjustText] = useState("");
  const [reviewNote, setReviewNote] = useState("");
  const [adjustError, setAdjustError] = useState<string | null>(null);
  const [activity, setActivity] = useState<GraphActivityEntry[]>([]);
  const [ui, setUi] = useState<UiState>({ status: "idle" });
  const [isPending, startTransition] = useTransition();
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const isLoading = ui.status === "loading" || isPending;
  const reviewData = ui.status === "awaiting_review" ? ui.data : null;

  const applyError = (err: unknown, question?: string) => {
    if (err instanceof AnswerApiError) {
      setUi({
        status: "error",
        question,
        message: err.message,
        kind: err.kind,
        httpStatus: err.status,
      });
      return;
    }
    setUi({
      status: "error",
      question,
      message: err instanceof Error ? err.message : "Error inesperado",
      kind: "http",
      httpStatus: null,
    });
  };

  const submitQuestion = (value: string) => {
    const question = value.trim();
    if (!question || isLoading) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setDraft("");
    setAdjustText("");
    setReviewNote("");
    setAdjustError(null);
    setActivity([]);
    setUi({ status: "loading", question });
    void (async () => {
      try {
        const data = await runAgenticWithProgress(
          { question },
          {
            signal: controller.signal,
            onProgress: (progress) => {
              setActivity(progress.activity);
            },
          },
        );
        const next = mapAgenticUi(question, data);
        if (next.status === "awaiting_review" && data.answer) {
          setAdjustText(data.answer);
        }
        setUi(next);
      } catch (err) {
        if (controller.signal.aborted) return;
        applyError(err, question);
      }
    })();
  };

  const resume = (decision: "approve" | "reject" | "adjust") => {
    if (!reviewData || isLoading) return;
    if (decision === "adjust" && !adjustText.trim()) {
      setAdjustError("Para ajustar, editá la respuesta antes de enviar.");
      return;
    }

    const question =
      ui.status === "awaiting_review" ? ui.question : reviewData.question;
    const threadId = reviewData.thread_id;
    setAdjustError(null);
    setUi({ status: "loading", question });
    startTransition(async () => {
      try {
        const data = await resumeAgenticAnswer(threadId, {
          decision,
          ...(reviewNote.trim() ? { note: reviewNote.trim() } : {}),
          ...(decision === "adjust"
            ? { adjusted_answer: adjustText.trim() }
            : {}),
        });
        setUi(mapAgenticUi(question, data));
      } catch (err) {
        applyError(err, question);
      }
    });
  };

  const activeQuestion =
    ui.status === "loading" ||
    ui.status === "completed" ||
    ui.status === "awaiting_review" ||
    ui.status === "rejected"
      ? ui.question
      : ui.status === "error"
        ? ui.question
        : undefined;

  const resultData =
    ui.status === "completed" ||
    ui.status === "awaiting_review" ||
    ui.status === "rejected"
      ? ui.data
      : null;

  const hasTranscript = Boolean(activeQuestion);
  const liveCalls = isLoading ? buildLiveCalls(activity) : [];
  const finishedCalls = resultData ? buildTraceCalls(resultData) : [];

  return (
    <Layout
      height="fill"
      padding={0}
      content={
        <LayoutContent padding={0}>
          <ChatLayout
            density="spacious"
            emptyState={
              !hasTranscript ? (
                <VStack gap={8} align="center">
                  <EmptyState
                    title="Preguntá sobre Metropol Fintech"
                    description="El pipeline planifica, recupera evidencia, sintetiza y valida citas. Mientras corre vas a ver el progreso de cada agente. Si la confianza es baja, el turno se pausa para revisión humana."
                    headingLevel={1}
                  />
                  <Grid columns={{ minWidth: 220, max: 3 }} gap={2}>
                    {SUGGESTIONS.map((suggestion) => (
                      <ClickableCard
                        key={suggestion}
                        label={suggestion}
                        variant="muted"
                        padding={3}
                        isDisabled={isLoading}
                        onClick={() => submitQuestion(suggestion)}
                      >
                        <Text type="body" textWrap="pretty">
                          {suggestion}
                        </Text>
                      </ClickableCard>
                    ))}
                  </Grid>
                </VStack>
              ) : undefined
            }
            composer={
              <VStack gap={3}>
                {ui.status === "error" ? (
                  <Banner
                    status="error"
                    title={
                      ui.kind === "unavailable"
                        ? "Servicio no disponible"
                        : ui.httpStatus === 404
                          ? "Thread no disponible"
                          : "No se pudo completar la corrida"
                    }
                    description={ui.message}
                  />
                ) : null}

                {reviewData ? (
                  <VStack gap={4}>
                    <Banner
                      status="warning"
                      title="Esta respuesta necesita revisión humana"
                      description={
                        reviewData.review_reasons.length > 0
                          ? reviewData.review_reasons.join(" · ")
                          : "La corrida pidió revisión antes de cerrar."
                      }
                    />
                    <VStack gap={1}>
                      {reviewData.confidence != null ? (
                        <Text type="supporting" color="secondary">
                          Confianza{" "}
                          <Text as="span" weight="semibold" color="primary">
                            {Math.round(reviewData.confidence * 100)}%
                          </Text>
                        </Text>
                      ) : null}
                      <Text type="supporting" color="secondary">
                        thread: {reviewData.thread_id}
                        {reviewData.no_evidence ? " · sin evidencia" : ""}
                      </Text>
                    </VStack>

                    {reviewData.answer ? (
                      <ChatMessageBubble variant="ghost" width="100%">
                        <Markdown density="compact" headingLevelStart={3}>
                          {reviewData.answer}
                        </Markdown>
                      </ChatMessageBubble>
                    ) : null}

                    {adjustError ? (
                      <Banner
                        status="error"
                        title="Falta el ajuste"
                        description={adjustError}
                      />
                    ) : null}

                    <TextArea
                      label="Nota para el registro (opcional)"
                      value={reviewNote}
                      onChange={setReviewNote}
                      isDisabled={isLoading}
                      placeholder="p. ej. revisado con el equipo de negocio"
                    />
                    <TextArea
                      label="Ajustar respuesta"
                      value={adjustText}
                      onChange={(v) => {
                        setAdjustText(v);
                        setAdjustError(null);
                      }}
                      isDisabled={isLoading}
                      isOptional
                      description="Solo se envía si elegís Ajustar."
                      placeholder="Editá el borrador antes de ajustar…"
                    />
                    <HStack gap={3} wrap="wrap">
                      <Button
                        label={isLoading ? "Enviando…" : "Aprobar"}
                        variant="primary"
                        isDisabled={isLoading}
                        isLoading={isLoading}
                        onClick={() => resume("approve")}
                      />
                      <Button
                        label="Ajustar"
                        variant="secondary"
                        isDisabled={isLoading || !adjustText.trim()}
                        onClick={() => resume("adjust")}
                      />
                      <Button
                        label="Rechazar"
                        variant="ghost"
                        isDisabled={isLoading}
                        onClick={() => resume("reject")}
                      />
                    </HStack>
                  </VStack>
                ) : null}

                <ChatComposer
                  value={draft}
                  onChange={setDraft}
                  onSubmit={submitQuestion}
                  isDisabled={isLoading || reviewData != null}
                  placeholder="Escribí una pregunta sobre el corpus…"
                  input={<ChatComposerInput />}
                />
                <Text
                  type="supporting"
                  color="secondary"
                  justify="center"
                  display="block"
                >
                  Cada envío es una corrida nueva. El progreso de agentes se
                  actualiza en vivo; si reiniciás el backend, el thread se
                  pierde.
                </Text>
              </VStack>
            }
          >
            {hasTranscript ? (
              <ChatMessageList>
                <ChatSystemMessage variant="divider">Hoy</ChatSystemMessage>

                <ChatMessage sender="user">
                  <ChatMessageBubble>{activeQuestion}</ChatMessageBubble>
                </ChatMessage>

                {isLoading ? (
                  <ChatMessage
                    sender="assistant"
                    avatar={<Avatar name="Metropol" size="md" />}
                  >
                    <ChatToolCalls
                      defaultIsExpanded
                      label="Flujo en vivo"
                      calls={liveCalls}
                    />
                    <ChatMessageBubble variant="ghost">
                      <Text type="body" color="secondary">
                        Corriendo pipeline agentic…
                      </Text>
                    </ChatMessageBubble>
                  </ChatMessage>
                ) : null}

                {resultData && !isLoading ? (
                  <ChatMessage
                    sender="assistant"
                    avatar={<Avatar name="Metropol" size="md" />}
                  >
                    {finishedCalls.length > 0 ? (
                      <ChatToolCalls
                        defaultIsExpanded={ui.status === "awaiting_review"}
                        label="Pasos del agente"
                        calls={finishedCalls}
                      />
                    ) : null}

                    {resultData.answer ? (
                      <ChatMessageBubble variant="ghost" width="100%">
                        <Markdown density="compact" headingLevelStart={3}>
                          {resultData.answer}
                        </Markdown>
                      </ChatMessageBubble>
                    ) : ui.status === "rejected" ? (
                      <ChatMessageBubble variant="ghost">
                        <Text type="body" color="secondary">
                          Corrida rechazada. No hay respuesta publicada.
                        </Text>
                      </ChatMessageBubble>
                    ) : ui.status === "awaiting_review" ? (
                      <ChatMessageBubble variant="ghost">
                        <Text type="body" color="secondary">
                          Borrador en pausa — revisá el panel debajo del
                          composer.
                        </Text>
                      </ChatMessageBubble>
                    ) : null}

                    {resultData.citations.length > 0 ? (
                      <ChatMessageBubble variant="ghost" width="100%">
                        <List
                          header={
                            <Heading level={3}>
                              Evidencia ({resultData.citations.length})
                            </Heading>
                          }
                          hasDividers
                          density="compact"
                        >
                          {resultData.citations.map((c) => (
                            <ListItem
                              key={`${c.document_id}-${c.chunk_id}`}
                              label={c.source_path}
                              description={c.excerpt}
                            />
                          ))}
                        </List>
                      </ChatMessageBubble>
                    ) : null}

                    <ChatMessageMetadata
                      footer={
                        <Text type="supporting" color="secondary">
                          {resultData.status === "completed"
                            ? "Completada"
                            : resultData.status === "awaiting_human_review"
                              ? "En revisión"
                              : "Rechazada"}
                          {resultData.prompt_version
                            ? ` · ${resultData.prompt_version}`
                            : ""}
                        </Text>
                      }
                    />
                  </ChatMessage>
                ) : null}

                {ui.status === "completed" && resultData?.no_evidence ? (
                  <ChatSystemMessage>
                    Sin evidencia suficiente en el corpus para esta pregunta.
                  </ChatSystemMessage>
                ) : null}
              </ChatMessageList>
            ) : null}
          </ChatLayout>
        </LayoutContent>
      }
    />
  );
}
