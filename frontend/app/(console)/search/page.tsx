"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

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
import { NumberInput } from "@astryxdesign/core/NumberInput";
import { Text } from "@astryxdesign/core/Text";
import { TextInput } from "@astryxdesign/core/TextInput";
import { Search } from "lucide-react";

import { AnswerApiError } from "../../lib/api/answer";
import {
  postSearch,
  type SearchHit,
  type SearchResponse,
} from "../../lib/api/search";

function leafPath(path: string): string {
  const parts = path.split("/");
  return parts[parts.length - 1] || path;
}

function HitRow({ hit, index }: { hit: SearchHit; index: number }) {
  const score = Number.isFinite(hit.score) ? hit.score.toFixed(3) : "—";
  const excerpt = (hit.content || "").trim();
  return (
    <ListItem
      label={`${index + 1}. ${leafPath(hit.source_path)}`}
      description={
        <VStack gap={2}>
          <HStack gap={2} wrap="wrap" align="center">
            <Badge variant="neutral" label={`score ${score}`} />
            <Text type="supporting" color="secondary">
              chunk {hit.chunk_id} · doc {hit.document_id} · {hit.chunk_type}
            </Text>
          </HStack>
          <Text type="supporting" color="secondary">
            {hit.source_path}
          </Text>
          <Text type="body">{excerpt || "(sin contenido)"}</Text>
        </VStack>
      }
    />
  );
}

function SearchConsoleInner() {
  const searchParams = useSearchParams();
  const initialQ = (searchParams.get("q") || "").trim();
  const [query, setQuery] = useState(initialQ);
  const [k, setK] = useState<number>(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const autoRan = useRef(false);

  const runSearch = useCallback(async (q: string, topK: number) => {
    const cleaned = q.trim();
    if (!cleaned) {
      setError("Escribí una consulta no vacía.");
      return;
    }
    setLoading(true);
    setError(null);
    setHasSearched(true);
    try {
      const data = await postSearch({ query: cleaned, k: topK });
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(
        err instanceof AnswerApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "No se pudo buscar",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (autoRan.current || !initialQ) return;
    autoRan.current = true;
    void runSearch(initialQ, k);
  }, [initialQ, k, runSearch]);

  const onSubmit = () => {
    void runSearch(query, k);
  };

  return (
    <Layout
      height="fill"
      padding={0}
      content={
        <LayoutContent padding={6} isScrollable>
          <VStack gap={6}>
            <VStack gap={2}>
              <Heading level={1}>Búsqueda semántica</Heading>
              <Text color="secondary">
                Inspeccioná hits del corpus Metropol sin generar una respuesta
                agentic. Útil para depurar retrieve y demos de RAG.
              </Text>
            </VStack>

            <HStack gap={3} wrap="wrap" align="end">
              <TextInput
                label="Consulta"
                value={query}
                onChange={setQuery}
                placeholder="p. ej. handoff cobranzas Tenela"
                width="100%"
                hasClear
                onEnter={onSubmit}
                startIcon={Search}
              />
              <NumberInput
                label="k"
                value={k}
                onChange={(value) => setK(value)}
                min={1}
                max={50}
                isIntegerOnly
                hasNumberSteppers
                width={120}
                description="Top hits"
              />
              <Button
                label={loading ? "Buscando…" : "Buscar"}
                variant="primary"
                isDisabled={loading || !query.trim()}
                isLoading={loading}
                onClick={onSubmit}
              />
            </HStack>

            {error ? (
              <Banner status="error" title="Búsqueda" description={error} />
            ) : null}

            {result ? (
              <VStack gap={3}>
                <HStack gap={2} wrap="wrap" align="center">
                  <Text type="supporting" color="secondary">
                    {result.results.length} hit
                    {result.results.length === 1 ? "" : "s"} · k={result.k} ·{" "}
                    {result.search_time_ms} ms
                  </Text>
                  <Badge variant="teal" label={result.query} />
                </HStack>

                {result.results.length === 0 ? (
                  <EmptyState
                    title="Sin resultados"
                    description="La API respondió OK pero no hay chunks cercanos. Probá otra consulta o revisá que el corpus esté ingerido."
                  />
                ) : (
                  <List
                    header="Hits"
                    hasDividers
                    density="spacious"
                    listStyle="none"
                  >
                    {result.results.map((hit, index) => (
                      <HitRow key={`${hit.chunk_id}-${index}`} hit={hit} index={index} />
                    ))}
                  </List>
                )}
              </VStack>
            ) : null}

            {!hasSearched && !loading && !error ? (
              <EmptyState
                title="Todavía no buscaste"
                description="Escribí una consulta y tocá Buscar, o abrí /search?q=tu+consulta."
              />
            ) : null}
          </VStack>
        </LayoutContent>
      }
    />
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <Layout
          height="fill"
          padding={0}
          content={
            <LayoutContent padding={6}>
              <Text color="secondary">Cargando consola de búsqueda…</Text>
            </LayoutContent>
          }
        />
      }
    >
      <SearchConsoleInner />
    </Suspense>
  );
}
