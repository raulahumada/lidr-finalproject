"use client";

import {
  Suspense,
  useCallback,
  useEffect,
  useRef,
  useState,
  useTransition,
} from "react";
import { useSearchParams } from "next/navigation";

import { Avatar } from "@astryxdesign/core/Avatar";
import { Badge } from "@astryxdesign/core/Badge";
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
import { Selector } from "@astryxdesign/core/Selector";
import { Text } from "@astryxdesign/core/Text";
import { TextArea } from "@astryxdesign/core/TextArea";

import { AnswerApiError } from "../lib/api/answer";
import {
  resumeAgenticAnswer,
  runAgenticWithProgress,
  type AgenticAnswerResponse,
  type GraphActivityEntry,
  type MetropolDomain,
  type RoutingHistoryEntry,
} from "../lib/api/agentic";
import { readAnswerSession, type HistoryTurn } from "../lib/api/sessions";
import { useChatSessions } from "../lib/chat-sessions-context";

const SUGGESTIONS = [
  "¿Cómo es el handoff de cobranzas con Tenela?",
  "¿Qué canales cubre la omnicanalidad de Metropol?",
  "¿Cómo se gestiona el proceso de ventas?",
];

const DOMAIN_OPTIONS = [
  { value: "auto", label: "Auto (detectar)" },
  { value: "ventas", label: "Ventas" },
  { value: "cobranzas", label: "Cobranzas" },
  { value: "operacion", label: "Operación" },
  { value: "tenela", label: "Tenela" },
  { value: "general", label: "General" },
] as const;

const PIPELINE_NODES = [
  { node: "orchestrator", label: "Orquestador" },
  { node: "intent_framer", label: "Encuadre de intención" },
  { node: "corpus_fetcher", label: "Recuperación de evidencia" },
  { node: "grounded_composer", label: "Síntesis grounded" },
  { node: "source_guard", label: "Validación de citas" },
  { node: "escalation_gate", label: "Gate de revisión" },
] as const;

type DomainChoice = "auto" | MetropolDomain;

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

type StashedSessionUi = {
  ui: UiState;
  activity: GraphActivityEntry[];
  adjustText: string;
  reviewNote: string;
  adjustError: string | null;
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

function AnswerPageInner() {
  const searchParams = useSearchParams();
  const sessionFromUrl = searchParams.get("session");
  const {
    refreshSessions,
    markBusy,
    busySessionIds,
    createSessionAndOpen,
    openSession,
  } = useChatSessions();

  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [historyTurns, setHistoryTurns] = useState<HistoryTurn[]>([]);
  const [sessionBootError, setSessionBootError] = useState<string | null>(null);

  const [draft, setDraft] = useState("");
  const [domainChoice, setDomainChoice] = useState<DomainChoice>("auto");
  const [adjustText, setAdjustText] = useState("");
  const [reviewNote, setReviewNote] = useState("");
  const [adjustError, setAdjustError] = useState<string | null>(null);
  const [activity, setActivity] = useState<GraphActivityEntry[]>([]);
  const [liveDomain, setLiveDomain] = useState<string | null>(null);
  const [liveRouting, setLiveRouting] = useState<RoutingHistoryEntry[]>([]);
  const [ui, setUi] = useState<UiState>({ status: "idle" });
  const [isPending, startTransition] = useTransition();

  const activeSessionIdRef = useRef<string | null>(null);
  const stashRef = useRef<Record<string, StashedSessionUi>>({});
  const controllersRef = useRef<Map<string, AbortController>>(new Map());

  useEffect(() => {
    activeSessionIdRef.current = activeSessionId;
  }, [activeSessionId]);

  useEffect(() => {
    return () => {
      for (const controller of controllersRef.current.values()) {
        controller.abort();
      }
      controllersRef.current.clear();
    };
  }, []);

  const stashActiveUi = useCallback(() => {
    if (!activeSessionIdRef.current) return;
    stashRef.current[activeSessionIdRef.current] = {
      ui,
      activity,
      adjustText,
      reviewNote,
      adjustError,
    };
  }, [ui, activity, adjustText, reviewNote, adjustError]);

  const applyStashOrIdle = useCallback((sessionId: string) => {
    const cached = stashRef.current[sessionId];
    if (!cached) {
      setUi({ status: "idle" });
      setActivity([]);
      setAdjustText("");
      setReviewNote("");
      setAdjustError(null);
      return;
    }
    setUi(cached.ui);
    setActivity(cached.activity);
    setAdjustText(cached.adjustText);
    setReviewNote(cached.reviewNote);
    setAdjustError(cached.adjustError);
  }, []);

  const loadSessionView = useCallback(async (sessionId: string) => {
    const view = await readAnswerSession(sessionId);
    setActiveSessionId(view.session_id);
    setHistoryTurns(view.history);
    setSessionBootError(null);
    return view;
  }, []);

  /** Boot / react to sidebar navigation (?session=). Never aborts in-flight runs. */
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        if (sessionFromUrl) {
          if (sessionFromUrl === activeSessionIdRef.current) return;
          stashActiveUi();
          await loadSessionView(sessionFromUrl);
          if (cancelled) return;
          const cached = stashRef.current[sessionFromUrl];
          const stillBusy = busySessionIds.has(sessionFromUrl);
          if (
            cached &&
            (cached.ui.status === "awaiting_review" ||
              (cached.ui.status === "loading" && stillBusy))
          ) {
            applyStashOrIdle(sessionFromUrl);
          } else {
            delete stashRef.current[sessionFromUrl];
            setUi({ status: "idle" });
            setActivity([]);
            setAdjustText("");
            setReviewNote("");
            setAdjustError(null);
          }
          return;
        }

        const list = await refreshSessions();
        if (cancelled) return;
        if (list.length === 0) {
          await createSessionAndOpen();
          return;
        }
        openSession(list[0].session_id);
      } catch (err) {
        if (cancelled) return;
        setSessionBootError(
          err instanceof AnswerApiError
            ? err.message
            : "No se pudo cargar la sesión.",
        );
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only when URL session changes
  }, [sessionFromUrl]);

  const isCurrentBusy = ui.status === "loading" || isPending;
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

  const ensureSessionId = async (): Promise<string> => {
    if (activeSessionId) return activeSessionId;
    return createSessionAndOpen();
  };

  const submitQuestion = (value: string) => {
    const question = value.trim();
    if (!question || isCurrentBusy) return;

    setDraft("");
    setAdjustText("");
    setReviewNote("");
    setAdjustError(null);
    setActivity([]);
    setLiveDomain(null);
    setLiveRouting([]);
    setUi({ status: "loading", question });

    void (async () => {
      let sessionId = "";
      try {
        sessionId = await ensureSessionId();
        const previous = controllersRef.current.get(sessionId);
        previous?.abort();
        const controller = new AbortController();
        controllersRef.current.set(sessionId, controller);

        markBusy(sessionId, true);
        const data = await runAgenticWithProgress(
          {
            question,
            session_id: sessionId,
            ...(domainChoice !== "auto" ? { domain: domainChoice } : {}),
          },
          {
            signal: controller.signal,
            onProgress: (progress) => {
              if (activeSessionIdRef.current === sessionId) {
                setActivity(progress.activity);
                setLiveDomain(progress.domain);
                setLiveRouting(progress.routing_history || []);
              } else {
                const stash = stashRef.current[sessionId];
                if (stash && stash.ui.status === "loading") {
                  stashRef.current[sessionId] = {
                    ...stash,
                    activity: progress.activity,
                  };
                }
              }
            },
          },
        );
        controllersRef.current.delete(sessionId);
        markBusy(sessionId, false);
        await refreshSessions();

        if (activeSessionIdRef.current !== sessionId) {
          if (data.status === "awaiting_human_review") {
            stashRef.current[sessionId] = {
              ui: mapAgenticUi(question, data),
              activity: [],
              adjustText: data.answer || "",
              reviewNote: "",
              adjustError: null,
            };
          } else {
            delete stashRef.current[sessionId];
          }
          return;
        }

        if (data.status === "awaiting_human_review") {
          if (data.answer) setAdjustText(data.answer);
          setUi(mapAgenticUi(question, data));
          return;
        }
        await loadSessionView(sessionId);
        setUi({ status: "idle" });
        delete stashRef.current[sessionId];
      } catch (err) {
        if (sessionId) {
          controllersRef.current.delete(sessionId);
          markBusy(sessionId, false);
        }
        if (err instanceof AnswerApiError && err.message === "Corrida cancelada") {
          return;
        }
        if (sessionId && activeSessionIdRef.current !== sessionId) return;
        applyError(err, question);
      }
    })();
  };

  const resume = (decision: "approve" | "reject" | "adjust") => {
    if (!reviewData || isCurrentBusy) return;
    if (decision === "adjust" && !adjustText.trim()) {
      setAdjustError("Para ajustar, editá la respuesta antes de enviar.");
      return;
    }

    const question =
      ui.status === "awaiting_review" ? ui.question : reviewData.question;
    const threadId = reviewData.thread_id;
    const sessionId = activeSessionId;
    setAdjustError(null);
    setUi({ status: "loading", question });
    if (sessionId) markBusy(sessionId, true);

    startTransition(async () => {
      try {
        const data = await resumeAgenticAnswer(threadId, {
          decision,
          ...(reviewNote.trim() ? { note: reviewNote.trim() } : {}),
          ...(decision === "adjust"
            ? { adjusted_answer: adjustText.trim() }
            : {}),
        });
        if (sessionId) markBusy(sessionId, false);
        await refreshSessions();

        if (sessionId && activeSessionIdRef.current !== sessionId) {
          if (data.status === "awaiting_human_review") {
            stashRef.current[sessionId] = {
              ui: mapAgenticUi(question, data),
              activity: [],
              adjustText: data.answer || "",
              reviewNote: "",
              adjustError: null,
            };
          } else {
            delete stashRef.current[sessionId];
          }
          return;
        }

        if (sessionId) await loadSessionView(sessionId);
        if (data.status === "awaiting_human_review") {
          setUi(mapAgenticUi(question, data));
        } else {
          setUi({ status: "idle" });
          if (sessionId) delete stashRef.current[sessionId];
        }
      } catch (err) {
        if (sessionId) markBusy(sessionId, false);
        if (sessionId && activeSessionIdRef.current !== sessionId) return;
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

  const hasTranscript =
    historyTurns.length > 0 || Boolean(activeQuestion) || ui.status === "error";
  const liveCalls = isCurrentBusy ? buildLiveCalls(activity) : [];
  const finishedCalls = resultData ? buildTraceCalls(resultData) : [];
  const shownDomain = resultData?.domain ?? liveDomain;
  const shownRouting =
    resultData?.routing_history?.length
      ? resultData.routing_history
      : liveRouting;

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
                    description="Las sesiones viven en el menú lateral. Podés cambiar de chat mientras corre una respuesta: no se cancela; al volver ves el resultado."
                    headingLevel={1}
                  />
                  {sessionBootError ? (
                    <Banner
                      status="error"
                      title="Sesiones"
                      description={sessionBootError}
                    />
                  ) : null}
                  <Grid columns={{ minWidth: 220, max: 3 }} gap={2}>
                    {SUGGESTIONS.map((suggestion) => (
                      <ClickableCard
                        key={suggestion}
                        label={suggestion}
                        variant="muted"
                        padding={3}
                        isDisabled={isCurrentBusy || !activeSessionId}
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
                          ? "Recurso no disponible"
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
                      isDisabled={isCurrentBusy}
                      placeholder="p. ej. revisado con el equipo de negocio"
                    />
                    <TextArea
                      label="Ajustar respuesta"
                      value={adjustText}
                      onChange={(v) => {
                        setAdjustText(v);
                        setAdjustError(null);
                      }}
                      isDisabled={isCurrentBusy}
                      isOptional
                      description="Solo se envía si elegís Ajustar."
                      placeholder="Editá el borrador antes de ajustar…"
                    />
                    <HStack gap={3} wrap="wrap">
                      <Button
                        label={isCurrentBusy ? "Enviando…" : "Aprobar"}
                        variant="primary"
                        isDisabled={isCurrentBusy}
                        isLoading={isCurrentBusy}
                        onClick={() => resume("approve")}
                      />
                      <Button
                        label="Ajustar"
                        variant="secondary"
                        isDisabled={isCurrentBusy || !adjustText.trim()}
                        onClick={() => resume("adjust")}
                      />
                      <Button
                        label="Rechazar"
                        variant="ghost"
                        isDisabled={isCurrentBusy}
                        onClick={() => resume("reject")}
                      />
                    </HStack>
                  </VStack>
                ) : null}

                <HStack gap={3} wrap="wrap" align="end">
                  <Selector
                    label="Dominio"
                    options={[...DOMAIN_OPTIONS]}
                    value={domainChoice}
                    onChange={(value) =>
                      setDomainChoice((value as DomainChoice) || "auto")
                    }
                    size="sm"
                    width={200}
                    isDisabled={
                      isCurrentBusy || reviewData != null || !activeSessionId
                    }
                    description="Auto detecta; override fuerza el tag Metropol."
                  />
                </HStack>

                <ChatComposer
                  value={draft}
                  onChange={setDraft}
                  onSubmit={submitQuestion}
                  isDisabled={
                    isCurrentBusy || reviewData != null || !activeSessionId
                  }
                  placeholder="Escribí una pregunta sobre el corpus…"
                  input={<ChatComposerInput />}
                />
              </VStack>
            }
          >
            {hasTranscript ? (
              <ChatMessageList>
                <ChatSystemMessage variant="divider">
                  {activeSessionId
                    ? `Sesión ${activeSessionId.slice(0, 8)}`
                    : "Hoy"}
                </ChatSystemMessage>

                {historyTurns.map((turn, index) => (
                  <VStack
                    key={`${turn.thread_id ?? "turn"}-${index}`}
                    gap={2}
                  >
                    <ChatMessage sender="user">
                      <ChatMessageBubble>{turn.question}</ChatMessageBubble>
                    </ChatMessage>
                    <ChatMessage
                      sender="assistant"
                      avatar={<Avatar name="Metropol" size="md" />}
                    >
                      {turn.answer ? (
                        <ChatMessageBubble variant="ghost" width="100%">
                          <Markdown density="compact" headingLevelStart={3}>
                            {turn.answer}
                          </Markdown>
                        </ChatMessageBubble>
                      ) : turn.status === "rejected" ? (
                        <ChatMessageBubble variant="ghost">
                          <Text type="body" color="secondary">
                            Corrida rechazada.
                          </Text>
                        </ChatMessageBubble>
                      ) : null}
                      {turn.citations.length > 0 ? (
                        <ChatMessageBubble variant="ghost" width="100%">
                          <List
                            header={
                              <Heading level={3}>
                                Evidencia ({turn.citations.length})
                              </Heading>
                            }
                            hasDividers
                            density="compact"
                          >
                            {turn.citations.map((c, ci) => (
                              <ListItem
                                key={`${c.document_id}-${c.chunk_id}-${ci}`}
                                label={c.source_path || "fuente"}
                                description={c.excerpt}
                              />
                            ))}
                          </List>
                        </ChatMessageBubble>
                      ) : null}
                      <ChatMessageMetadata
                        footer={
                          <Text type="supporting" color="secondary">
                            {turn.status === "completed"
                              ? "Completada"
                              : "Rechazada"}
                          </Text>
                        }
                      />
                    </ChatMessage>
                  </VStack>
                ))}

                {activeQuestion ? (
                  <>
                    <ChatMessage sender="user">
                      <ChatMessageBubble>{activeQuestion}</ChatMessageBubble>
                    </ChatMessage>

                    {isCurrentBusy ? (
                      <ChatMessage
                        sender="assistant"
                        avatar={<Avatar name="Metropol" size="md" />}
                      >
                        {shownDomain ? (
                          <HStack gap={2} wrap="wrap">
                            <Badge variant="teal" label={shownDomain} />
                          </HStack>
                        ) : null}
                        <ChatToolCalls
                          defaultIsExpanded
                          label="Flujo en vivo"
                          calls={liveCalls}
                        />
                        {shownRouting.length > 0 ? (
                          <ChatMessageBubble variant="ghost" width="100%">
                            <List
                              header={
                                <Heading level={3}>Ruteo</Heading>
                              }
                              hasDividers
                              density="compact"
                            >
                              {shownRouting.map((step) => (
                                <ListItem
                                  key={`route-${step.step}-${step.next_agent}`}
                                  label={`→ ${step.next_agent}`}
                                  description={
                                    step.reason
                                      ? `${step.reason}${step.source ? ` (${step.source})` : ""}`
                                      : step.source || undefined
                                  }
                                />
                              ))}
                            </List>
                          </ChatMessageBubble>
                        ) : null}
                        <ChatMessageBubble variant="ghost">
                          <Text type="body" color="secondary">
                            Corriendo pipeline agentic…
                          </Text>
                        </ChatMessageBubble>
                      </ChatMessage>
                    ) : null}

                    {resultData && !isCurrentBusy ? (
                      <ChatMessage
                        sender="assistant"
                        avatar={<Avatar name="Metropol" size="md" />}
                      >
                        {shownDomain ? (
                          <HStack gap={2} wrap="wrap">
                            <Badge variant="teal" label={shownDomain} />
                          </HStack>
                        ) : null}
                        {finishedCalls.length > 0 ? (
                          <ChatToolCalls
                            defaultIsExpanded={ui.status === "awaiting_review"}
                            label="Pasos del agente"
                            calls={finishedCalls}
                          />
                        ) : null}
                        {shownRouting.length > 0 ? (
                          <ChatMessageBubble variant="ghost" width="100%">
                            <List
                              header={
                                <Heading level={3}>Ruteo</Heading>
                              }
                              hasDividers
                              density="compact"
                            >
                              {shownRouting.map((step) => (
                                <ListItem
                                  key={`done-route-${step.step}-${step.next_agent}`}
                                  label={`→ ${step.next_agent}`}
                                  description={
                                    step.reason
                                      ? `${step.reason}${step.source ? ` (${step.source})` : ""}`
                                      : step.source || undefined
                                  }
                                />
                              ))}
                            </List>
                          </ChatMessageBubble>
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

                        <ChatMessageMetadata
                          footer={
                            <Text type="supporting" color="secondary">
                              {resultData.status === "completed"
                                ? "Completada"
                                : resultData.status === "awaiting_human_review"
                                  ? "En revisión"
                                  : "Rechazada"}
                            </Text>
                          }
                        />
                      </ChatMessage>
                    ) : null}
                  </>
                ) : null}
              </ChatMessageList>
            ) : null}
          </ChatLayout>
        </LayoutContent>
      }
    />
  );
}

export default function AnswerPage() {
  return (
    <Suspense
      fallback={
        <Layout
          height="fill"
          padding={6}
          content={
            <LayoutContent>
              <Text type="body" color="secondary">
                Cargando chat…
              </Text>
            </LayoutContent>
          }
        />
      }
    >
      <AnswerPageInner />
    </Suspense>
  );
}
