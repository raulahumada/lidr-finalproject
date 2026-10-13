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
import { Switch } from "@astryxdesign/core/Switch";
import { Text } from "@astryxdesign/core/Text";
import { Database, Search } from "lucide-react";

import { AnswerApiError } from "../lib/api/answer";
import {
  getIngestStats,
  runIngestWithProgress,
  type IngestRunView,
  type IngestStats,
  type IngestSummary,
} from "../lib/api/ingest";

function SummaryBlock({ summary }: { summary: IngestSummary }) {
  return (
    <VStack gap={3}>
      <HStack gap={2} wrap="wrap">
        <Badge variant="neutral" label={`seen ${summary.seen}`} />
        <Badge variant="teal" label={`ingested ${summary.ingested}`} />
        <Badge variant="neutral" label={`chunks ${summary.chunks}`} />
        <Badge
          variant="neutral"
          label={`skip ext ${summary.skipped_extension}`}
        />
        <Badge
          variant="neutral"
          label={`skip existing ${summary.skipped_existing}`}
        />
        <Badge variant="neutral" label={`failed ${summary.failed}`} />
      </HStack>
      {summary.errors.length > 0 ? (
        <List>
          {summary.errors.slice(0, 12).map((err) => (
            <ListItem key={err} label={err} />
          ))}
        </List>
      ) : null}
    </VStack>
  );
}

export default function IngestPage() {
  const [stats, setStats] = useState<IngestStats | null>(null);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [force, setForce] = useState(false);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [runView, setRunView] = useState<IngestRunView | null>(null);

  const loadStats = useCallback(async () => {
    setStatsError(null);
    try {
      setStats(await getIngestStats());
    } catch (err) {
      setStats(null);
      setStatsError(
        err instanceof AnswerApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "No se pudieron cargar las stats",
      );
    }
  }, []);

  useEffect(() => {
    void loadStats();
  }, [loadStats]);

  const onStart = async () => {
    setRunning(true);
    setRunError(null);
    setRunView(null);
    try {
      const final = await runIngestWithProgress(force, setRunView);
      if (final.status === "failed") {
        setRunError(final.error || "La ingesta falló.");
      } else {
        await loadStats();
      }
    } catch (err) {
      setRunError(
        err instanceof AnswerApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "No se pudo iniciar la ingesta",
      );
    } finally {
      setRunning(false);
    }
  };

  const corpusLabel = stats?.corpus_root?.trim()
    ? stats.corpus_root
    : "(CORPUS_ROOT no configurado)";

  return (
    <Layout
      height="fill"
      padding={0}
      content={
        <LayoutContent padding={6} isScrollable>
          <VStack gap={6}>
            <VStack gap={2}>
              <Heading level={1}>Ingesta de corpus</Heading>
              <Text color="secondary">
                Lanzá el pipeline Metropol (walk → parse → chunk → embed) sobre
                CORPUS_ROOT sin usar la terminal. Después podés verificar hits
                en Búsqueda.
              </Text>
            </VStack>

            {statsError ? (
              <Banner status="error" title="Stats" description={statsError} />
            ) : null}
            {runError ? (
              <Banner status="error" title="Ingesta" description={runError} />
            ) : null}

            {stats ? (
              <VStack gap={3}>
                <HStack gap={2} wrap="wrap" align="center">
                  <Badge
                    variant="teal"
                    label={`${stats.document_count} docs`}
                  />
                  <Badge
                    variant="neutral"
                    label={`${stats.chunk_count} chunks`}
                  />
                  <Badge
                    variant="neutral"
                    label={`allowlist ${stats.allowlist.join(", ") || "—"}`}
                  />
                </HStack>
                <Text type="supporting" color="secondary">
                  Root: {corpusLabel}
                </Text>
              </VStack>
            ) : !statsError ? (
              <Text color="secondary">Cargando stats…</Text>
            ) : (
              <EmptyState
                icon={<Database />}
                title="Sin stats"
                description="Configurá DATABASE_URL / CORPUS_ROOT en el backend y reintentá."
              />
            )}

            <VStack gap={4}>
              <Switch
                label="Force re-ingest"
                description="Borra y vuelve a indexar source_path ya existentes."
                value={force}
                onChange={setForce}
                isDisabled={running}
              />
              <HStack gap={3} wrap="wrap">
                <Button
                  label={running ? "Ingeriendo…" : "Ingerir corpus"}
                  variant="primary"
                  onClick={() => void onStart()}
                  isDisabled={running}
                />
                <Button
                  label="Actualizar stats"
                  variant="ghost"
                  onClick={() => void loadStats()}
                  isDisabled={running}
                />
              </HStack>
            </VStack>

            {runView ? (
              <VStack gap={3}>
                <HStack gap={2} wrap="wrap" align="center">
                  <Badge variant="neutral" label={`status ${runView.status}`} />
                  <Text type="supporting" color="secondary">
                    run {runView.run_id.slice(0, 8)}…
                  </Text>
                </HStack>
                {runView.summary ? (
                  <SummaryBlock summary={runView.summary} />
                ) : running ? (
                  <Text color="secondary">Esperando resumen…</Text>
                ) : null}
                {runView.status === "completed" && runView.summary ? (
                  <Button
                    label="Ir a búsqueda"
                    variant="secondary"
                    icon={<Search />}
                    href="/search"
                  />
                ) : null}
              </VStack>
            ) : null}
          </VStack>
        </LayoutContent>
      }
    />
  );
}
