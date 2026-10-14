"use client";

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@astryxdesign/core/Badge";
import { Banner } from "@astryxdesign/core/Banner";
import { Button } from "@astryxdesign/core/Button";
import { EmptyState } from "@astryxdesign/core/EmptyState";
import { Heading } from "@astryxdesign/core/Heading";
import {
  HStack,
  Layout,
  LayoutContent,
  VStack,
} from "@astryxdesign/core/Layout";
import { List, ListItem } from "@astryxdesign/core/List";
import { Selector } from "@astryxdesign/core/Selector";
import { Text } from "@astryxdesign/core/Text";
import { TextInput } from "@astryxdesign/core/TextInput";

import { AnswerApiError } from "../../../lib/api/answer";
import {
  getUsageSummary,
  type UsagePurpose,
  type UsageSummary,
} from "../../../lib/api/usage";

const NUMBER = new Intl.NumberFormat("es-AR");

const PURPOSE_OPTIONS = [
  { value: "", label: "Todos" },
  { value: "answer", label: "answer (sync)" },
  { value: "grounded_composer", label: "grounded_composer" },
  { value: "prompt_specialist", label: "prompt_specialist" },
];

function formatCount(value: number): string {
  return NUMBER.format(value);
}

/** Local datetime string → ISO for the summary API. */
function localToIso(local: string): string | undefined {
  const trimmed = local.trim();
  if (!trimmed) return undefined;
  const date = new Date(trimmed);
  if (Number.isNaN(date.getTime())) return undefined;
  return date.toISOString();
}

export default function UsagePage() {
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [fromLocal, setFromLocal] = useState("");
  const [toLocal, setToLocal] = useState("");
  const [purpose, setPurpose] = useState<UsagePurpose>("");
  const [sessionId, setSessionId] = useState("");

  const load = useCallback(async () => {
    setPending(true);
    setError(null);
    try {
      const next = await getUsageSummary({
        from: localToIso(fromLocal),
        to: localToIso(toLocal),
        purpose,
        sessionId,
      });
      setSummary(next);
    } catch (err) {
      // Keep last successful totals on 422 / transient errors.
      setError(
        err instanceof AnswerApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "No se pudo leer el uso.",
      );
    } finally {
      setPending(false);
    }
  }, [fromLocal, toLocal, purpose, sessionId]);

  useEffect(() => {
    void load();
    // Initial load only; filters apply via button.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Layout
      height="fill"
      padding={0}
      content={
        <LayoutContent padding={6} isScrollable>
          <VStack gap={6}>
            <VStack gap={2}>
              <Heading level={1}>Uso de tokens</Heading>
              <Text color="secondary">
                Ledger de completions de chat (tokens reportados por el
                proveedor). Sin costo en USD.
              </Text>
            </VStack>

            {error ? (
              <Banner status="error" title="Uso" description={error} />
            ) : null}

            <HStack gap={3} wrap="wrap" align="end">
              <TextInput
                type="text"
                label="Desde"
                description="Fecha/hora local"
                value={fromLocal}
                onChange={setFromLocal}
                placeholder="2026-10-01T00:00"
              />
              <TextInput
                type="text"
                label="Hasta"
                description="Fecha/hora local"
                value={toLocal}
                onChange={setToLocal}
                placeholder="2026-10-14T23:59"
              />
              <Selector
                label="Purpose"
                value={purpose}
                onChange={(value) => setPurpose(value as UsagePurpose)}
                options={PURPOSE_OPTIONS}
              />
              <TextInput
                type="text"
                label="session_id"
                isOptional
                value={sessionId}
                onChange={setSessionId}
                placeholder="opcional"
              />
              <Button
                label={pending ? "Cargando…" : "Aplicar"}
                onClick={() => void load()}
                isDisabled={pending}
              />
            </HStack>

            {summary ? (
              <VStack gap={4}>
                <HStack gap={2} wrap="wrap">
                  <Badge
                    variant="teal"
                    label={`llamadas ${formatCount(summary.total_calls)}`}
                  />
                  <Badge
                    variant="neutral"
                    label={`input ${formatCount(summary.input_tokens)}`}
                  />
                  <Badge
                    variant="neutral"
                    label={`output ${formatCount(summary.output_tokens)}`}
                  />
                  <Badge
                    variant="neutral"
                    label={`total ${formatCount(summary.total_tokens)}`}
                  />
                </HStack>

                {summary.by_model.length === 0 ? (
                  <EmptyState
                    title="Sin eventos en esta ventana"
                    description="Probá ampliar el rango o quitá los filtros."
                  />
                ) : (
                  <VStack gap={2}>
                    <Heading level={2}>Por modelo</Heading>
                    <List>
                      {summary.by_model.map((row) => (
                        <ListItem
                          key={row.model}
                          label={row.model}
                          description={`${formatCount(row.calls)} llamadas · in ${formatCount(row.input_tokens)} · out ${formatCount(row.output_tokens)} · total ${formatCount(row.total_tokens)}`}
                        />
                      ))}
                    </List>
                  </VStack>
                )}
              </VStack>
            ) : !error ? (
              <Text color="secondary">Cargando resumen…</Text>
            ) : null}
          </VStack>
        </LayoutContent>
      }
    />
  );
}
