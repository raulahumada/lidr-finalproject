"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Badge } from "@astryxdesign/core/Badge";
import { Banner } from "@astryxdesign/core/Banner";
import { Button } from "@astryxdesign/core/Button";
import { ClickableCard } from "@astryxdesign/core/ClickableCard";
import { CodeBlock } from "@astryxdesign/core/CodeBlock";
import { Divider } from "@astryxdesign/core/Divider";
import { EmptyState } from "@astryxdesign/core/EmptyState";
import { Heading } from "@astryxdesign/core/Heading";
import {
  HStack,
  Layout,
  LayoutContent,
  LayoutPanel,
  VStack,
} from "@astryxdesign/core/Layout";
import { List, ListItem } from "@astryxdesign/core/List";
import {
  SegmentedControl,
  SegmentedControlItem,
} from "@astryxdesign/core/SegmentedControl";
import { Switch } from "@astryxdesign/core/Switch";
import { Text } from "@astryxdesign/core/Text";
import { TextArea } from "@astryxdesign/core/TextArea";
import { TextInput } from "@astryxdesign/core/TextInput";

import { AnswerApiError } from "../lib/api/answer";
import {
  createAgentProfile,
  deleteAgentProfile,
  fetchAgentCatalog,
  updateAgentProfile,
  type AgentCatalogEntry,
  type AgentCatalogResponse,
} from "../lib/api/agents";

type PanelTab = "detalle" | "crear";

type CreateForm = {
  key: string;
  label: string;
  role: string;
  system_prompt: string;
  enabled: boolean;
};

const emptyCreate = (): CreateForm => ({
  key: "",
  label: "",
  role: "",
  system_prompt: "",
  enabled: true,
});

function isCustom(agent: AgentCatalogEntry | null): boolean {
  if (!agent) return false;
  return agent.kind === "custom" || agent.mutable === true;
}

function agentByKey(
  catalog: AgentCatalogResponse | null,
  key: string,
): AgentCatalogEntry | undefined {
  return catalog?.agents.find((a) => a.key === key);
}

function FlowNode({
  agent,
  selected,
  hub,
  onSelect,
}: {
  agent: AgentCatalogEntry;
  selected: boolean;
  hub?: boolean;
  onSelect: () => void;
}) {
  const custom = isCustom(agent);
  return (
    <ClickableCard
      label={agent.label}
      onClick={onSelect}
      padding={3}
      variant={selected ? "teal" : hub ? "muted" : "default"}
      elevation={selected ? "low" : "none"}
      width={hub ? 220 : 160}
    >
      <VStack gap={2}>
        <HStack gap={2} wrap="wrap" align="center">
          <Text weight="semibold" type="body">
            {agent.label}
          </Text>
          <Badge
            variant={custom ? "teal" : hub ? "blue" : "neutral"}
            label={custom ? "custom" : hub ? "hub" : "builtin"}
          />
        </HStack>
        <Text type="supporting" color="secondary">
          {agent.key}
        </Text>
        <Badge
          variant={agent.llm_driven ? "orange" : "neutral"}
          label={agent.llm_driven ? "LLM + prompt" : "código"}
        />
      </VStack>
    </ClickableCard>
  );
}

function FlowArrow() {
  return (
    <Text type="supporting" color="secondary" weight="semibold">
      →
    </Text>
  );
}

export default function AgentsPage() {
  const [catalog, setCatalog] = useState<AgentCatalogResponse | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [tab, setTab] = useState<PanelTab>("detalle");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [createForm, setCreateForm] = useState<CreateForm>(emptyCreate);
  const [editForm, setEditForm] = useState<{
    label: string;
    role: string;
    system_prompt: string;
    enabled: boolean;
  } | null>(null);

  const refresh = useCallback(async () => {
    const data = await fetchAgentCatalog();
    setCatalog(data);
    setError(null);
    return data;
  }, []);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const data = await refresh();
        if (!cancelled && data.agents.length > 0) {
          setSelectedKey((prev) => prev ?? "orchestrator");
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
  }, [refresh]);

  const selected = agentByKey(catalog, selectedKey || "") ?? null;

  useEffect(() => {
    if (!isCustom(selected)) {
      setEditForm(null);
      return;
    }
    setEditForm({
      label: selected!.label,
      role: selected!.role,
      system_prompt: selected!.system_prompt || selected!.prompt_preview || "",
      enabled: selected!.enabled !== false,
    });
  }, [selected]);

  const ladderAgents = useMemo(() => {
    if (!catalog) return [];
    return catalog.ladder
      .map((key) => agentByKey(catalog, key))
      .filter((a): a is AgentCatalogEntry => Boolean(a));
  }, [catalog]);

  const hub = agentByKey(catalog, "orchestrator");
  const gate = agentByKey(catalog, "escalation_gate");

  const onCreate = async () => {
    setBusy(true);
    setError(null);
    try {
      const created = await createAgentProfile({
        key: createForm.key.trim(),
        label: createForm.label.trim(),
        role: createForm.role.trim(),
        system_prompt: createForm.system_prompt.trim(),
        enabled: createForm.enabled,
      });
      setCreateForm(emptyCreate());
      await refresh();
      setSelectedKey(created.key);
      setTab("detalle");
    } catch (err) {
      setError(
        err instanceof AnswerApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "No se pudo crear el agente",
      );
    } finally {
      setBusy(false);
    }
  };

  const onSaveCustom = async () => {
    if (!selected || !editForm || !isCustom(selected)) return;
    setBusy(true);
    setError(null);
    try {
      await updateAgentProfile(selected.key, {
        label: editForm.label.trim(),
        role: editForm.role.trim(),
        system_prompt: editForm.system_prompt.trim(),
        enabled: editForm.enabled,
      });
      await refresh();
    } catch (err) {
      setError(
        err instanceof AnswerApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "No se pudo guardar",
      );
    } finally {
      setBusy(false);
    }
  };

  const onDeleteCustom = async () => {
    if (!selected || !isCustom(selected)) return;
    setBusy(true);
    setError(null);
    try {
      await deleteAgentProfile(selected.key);
      const data = await refresh();
      setSelectedKey("orchestrator");
      if (!data.agents.some((a) => a.key === "orchestrator")) {
        setSelectedKey(data.agents[0]?.key ?? null);
      }
    } catch (err) {
      setError(
        err instanceof AnswerApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "No se pudo borrar",
      );
    } finally {
      setBusy(false);
    }
  };

  const selectNode = (key: string) => {
    setSelectedKey(key);
    setTab("detalle");
  };

  return (
    <Layout
      height="fill"
      padding={0}
      content={
        <LayoutContent padding={6} isScrollable>
          <VStack gap={6}>
            <VStack gap={2}>
              <Heading level={1}>Orquestación de agentes</Heading>
              <Text color="secondary">
                El hub elige el siguiente nodo de la escalera. Solo los nodos LLM
                tienen system prompt (composer Jinja o customs en DB).
              </Text>
            </VStack>

            {error ? (
              <Banner status="error" title="Agentes" description={error} />
            ) : null}

            {loading && !catalog ? (
              <Text type="body" color="secondary">
                Cargando grafo…
              </Text>
            ) : null}

            {catalog ? (
              <>
                <Banner
                  status="info"
                  title="¿Por qué casi nadie tiene system prompt?"
                  description="Orchestrator, framer, retrieve, guard y gate son código Python. Solo grounded_composer (Jinja) y los customs (Postgres) llaman al LLM con un system prompt."
                />

                <VStack gap={4}>
                  <Heading level={2}>Grafo (estrella)</Heading>
                  <Text type="supporting" color="secondary">
                    Tocá un nodo para inspeccionarlo. El orquestador vuelve a
                    decidir después de cada especialista.
                  </Text>

                  {hub ? (
                    <HStack gap={3} justify="center" wrap="wrap">
                      <FlowNode
                        agent={hub}
                        hub
                        selected={selectedKey === hub.key}
                        onSelect={() => selectNode(hub.key)}
                      />
                    </HStack>
                  ) : null}

                  <HStack gap={2} justify="center">
                    <Text type="supporting" color="secondary">
                      ↓ despacha / ← vuelve
                    </Text>
                  </HStack>

                  <HStack gap={2} align="center" wrap="wrap" justify="center">
                    {ladderAgents.map((agent, index) => (
                      <HStack key={agent.key} gap={2} align="center">
                        {index > 0 ? <FlowArrow /> : null}
                        <FlowNode
                          agent={agent}
                          selected={selectedKey === agent.key}
                          onSelect={() => selectNode(agent.key)}
                        />
                      </HStack>
                    ))}
                    {gate ? (
                      <HStack gap={2} align="center">
                        <FlowArrow />
                        <FlowNode
                          agent={gate}
                          selected={selectedKey === gate.key}
                          onSelect={() => selectNode(gate.key)}
                        />
                      </HStack>
                    ) : null}
                  </HStack>
                </VStack>

                <Divider label="Límites del servicio" />

                <HStack gap={6} wrap="wrap">
                  <VStack gap={1}>
                    <Text type="supporting" color="secondary">
                      max steps
                    </Text>
                    <Text weight="semibold">
                      {catalog.knobs.agentic_orchestrator_max_steps}
                    </Text>
                  </VStack>
                  <VStack gap={1}>
                    <Text type="supporting" color="secondary">
                      confidence threshold
                    </Text>
                    <Text weight="semibold">
                      {catalog.knobs.agentic_confidence_threshold}
                    </Text>
                  </VStack>
                </HStack>
              </>
            ) : null}
          </VStack>
        </LayoutContent>
      }
      end={
        <LayoutPanel width={420} hasDivider isScrollable label="Detalle de agente">
          <VStack gap={5} padding={4}>
            <SegmentedControl
              label="Vista del panel"
              value={tab}
              onChange={(value) => setTab(value as PanelTab)}
              layout="fill"
              size="sm"
            >
              <SegmentedControlItem value="detalle" label="Detalle" />
              <SegmentedControlItem value="crear" label="Crear custom" />
            </SegmentedControl>

            {tab === "crear" ? (
              <VStack gap={3}>
                <Heading level={2}>Nuevo agente LLM</Heading>
                <Text type="supporting" color="secondary">
                  Se guarda en Postgres y, si está enabled, entra al ladder
                  después de corpus_fetcher.
                </Text>
                <TextInput
                  label="Key (snake_case)"
                  value={createForm.key}
                  onChange={(v) => setCreateForm({ ...createForm, key: v })}
                  isDisabled={busy}
                  placeholder="risk_advisor"
                />
                <TextInput
                  label="Label"
                  value={createForm.label}
                  onChange={(v) => setCreateForm({ ...createForm, label: v })}
                  isDisabled={busy}
                />
                <TextArea
                  label="Rol"
                  value={createForm.role}
                  onChange={(v) => setCreateForm({ ...createForm, role: v })}
                  isDisabled={busy}
                  rows={2}
                />
                <TextArea
                  label="System prompt"
                  value={createForm.system_prompt}
                  onChange={(v) =>
                    setCreateForm({ ...createForm, system_prompt: v })
                  }
                  isDisabled={busy}
                  rows={8}
                />
                <Switch
                  label="Enabled en el ladder"
                  value={createForm.enabled}
                  onChange={(v) =>
                    setCreateForm({ ...createForm, enabled: v })
                  }
                  isDisabled={busy}
                />
                <Button
                  label={busy ? "Creando…" : "Crear agente"}
                  variant="primary"
                  isDisabled={
                    busy ||
                    !createForm.key.trim() ||
                    !createForm.label.trim() ||
                    !createForm.role.trim() ||
                    !createForm.system_prompt.trim()
                  }
                  isLoading={busy}
                  onClick={() => void onCreate()}
                />
              </VStack>
            ) : !selected ? (
              <EmptyState
                title="Elegí un nodo"
                description="Seleccioná un nodo del grafo para ver rol, implementación y prompt si aplica."
                headingLevel={2}
              />
            ) : (
              <VStack gap={4}>
                <VStack gap={2}>
                  <HStack gap={2} wrap="wrap" align="center">
                    <Heading level={2}>{selected.label}</Heading>
                    <Badge
                      variant={isCustom(selected) ? "teal" : "neutral"}
                      label={isCustom(selected) ? "custom" : "builtin"}
                    />
                    <Badge
                      variant={selected.llm_driven ? "orange" : "neutral"}
                      label={selected.llm_driven ? "LLM" : "código"}
                    />
                  </HStack>
                  <Text type="supporting" color="secondary">
                    <Text as="span" weight="semibold">
                      {selected.key}
                    </Text>
                    {" · "}
                    {selected.role}
                  </Text>
                </VStack>

                {selected.implementation ? (
                  <Banner
                    status="info"
                    title="Implementación"
                    description={selected.implementation}
                  />
                ) : null}

                {selected.tools.length > 0 ? (
                  <List
                    header={<Heading level={3}>Tools</Heading>}
                    hasDividers
                    density="compact"
                  >
                    {selected.tools.map((tool) => (
                      <ListItem key={tool} label={tool} />
                    ))}
                  </List>
                ) : null}

                {isCustom(selected) && editForm ? (
                  <VStack gap={3}>
                    <TextInput
                      label="Label"
                      value={editForm.label}
                      onChange={(v) =>
                        setEditForm({ ...editForm, label: v })
                      }
                      isDisabled={busy}
                    />
                    <TextArea
                      label="Rol"
                      value={editForm.role}
                      onChange={(v) => setEditForm({ ...editForm, role: v })}
                      isDisabled={busy}
                      rows={3}
                    />
                    <TextArea
                      label="System prompt (DB)"
                      value={editForm.system_prompt}
                      onChange={(v) =>
                        setEditForm({ ...editForm, system_prompt: v })
                      }
                      isDisabled={busy}
                      rows={12}
                    />
                    <Switch
                      label="Enabled en el ladder"
                      value={editForm.enabled}
                      onChange={(v) =>
                        setEditForm({ ...editForm, enabled: v })
                      }
                      isDisabled={busy}
                    />
                    <HStack gap={3} wrap="wrap">
                      <Button
                        label={busy ? "Guardando…" : "Guardar"}
                        variant="primary"
                        isDisabled={busy}
                        isLoading={busy}
                        onClick={() => void onSaveCustom()}
                      />
                      <Button
                        label="Eliminar"
                        variant="ghost"
                        isDisabled={busy}
                        onClick={() => void onDeleteCustom()}
                      />
                    </HStack>
                  </VStack>
                ) : selected.prompt_kind === "jinja" &&
                  selected.prompt_preview ? (
                  <VStack gap={3}>
                    <Text type="supporting" color="secondary">
                      {selected.prompt_note}
                      {selected.prompt_source
                        ? ` · ${selected.prompt_source}`
                        : ""}
                    </Text>
                    <CodeBlock
                      code={selected.prompt_preview}
                      language="jinja"
                      title="system.j2"
                      hasLineNumbers
                      isCollapsible
                      maxHeight={420}
                      width="100%"
                      size="sm"
                    />
                  </VStack>
                ) : (
                  <Banner
                    status="warning"
                    title="Sin system prompt"
                    description={
                      selected.prompt_note ||
                      "Este nodo no habla con el LLM; su comportamiento está en código Python."
                    }
                  />
                )}
              </VStack>
            )}
          </VStack>
        </LayoutPanel>
      }
    />
  );
}
