"use client";

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@astryxdesign/core/Badge";
import { Banner } from "@astryxdesign/core/Banner";
import { Button } from "@astryxdesign/core/Button";
import { Heading } from "@astryxdesign/core/Heading";
import {
  HStack,
  Layout,
  LayoutContent,
  VStack,
} from "@astryxdesign/core/Layout";
import { Selector } from "@astryxdesign/core/Selector";
import { Text } from "@astryxdesign/core/Text";

import { AnswerApiError } from "../lib/api/answer";
import {
  getModelsConfig,
  putModelsConfig,
  type ModelsConfig,
} from "../lib/api/config";

const ROLES: { key: string; label: string; description: string }[] = [
  {
    key: "chat",
    label: "Chat (sync /answer)",
    description: "Default y cascada para roles sin override propio.",
  },
  {
    key: "composer",
    label: "Composer (grounded)",
    description: "Síntesis grounded en el grafo agentic.",
  },
  {
    key: "prompt_specialist",
    label: "Prompt specialist (customs)",
    description: "Agentes custom del ladder.",
  },
];

/** Sentinel: clear override → use fallback chain / .env default */
const DEFAULT_VALUE = "__default__";

export default function SettingsPage() {
  const [config, setConfig] = useState<ModelsConfig | null>(null);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const applyConfig = useCallback((data: ModelsConfig) => {
    setConfig(data);
    const next: Record<string, string> = {};
    for (const role of ROLES) {
      const view = data.models[role.key];
      next[role.key] = view?.overridden ? view.effective : DEFAULT_VALUE;
    }
    setDraft(next);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      applyConfig(await getModelsConfig());
    } catch (err) {
      setConfig(null);
      setError(
        err instanceof AnswerApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "No se pudo cargar la config",
      );
    } finally {
      setLoading(false);
    }
  }, [applyConfig]);

  useEffect(() => {
    void load();
  }, [load]);

  const onSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    const models: Record<string, string | null> = {};
    for (const role of ROLES) {
      const value = draft[role.key] ?? DEFAULT_VALUE;
      models[role.key] = value === DEFAULT_VALUE ? null : value;
    }
    try {
      applyConfig(await putModelsConfig({ models }));
      setSuccess("Modelos guardados. Los próximos completes usan estos valores.");
    } catch (err) {
      setError(
        err instanceof AnswerApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "No se pudo guardar",
      );
    } finally {
      setSaving(false);
    }
  };

  const options = [
    { value: DEFAULT_VALUE, label: "Default (.env / cascada)" },
    ...(config?.available_models || []).map((m) => ({
      value: m,
      label: m,
    })),
  ];

  return (
    <Layout
      height="fill"
      padding={0}
      content={
        <LayoutContent padding={6} isScrollable>
          <VStack gap={6}>
            <VStack gap={2}>
              <Heading level={1}>Ajustes de modelos</Heading>
              <Text color="secondary">
                Overrides en caliente por rol (Redis). No reinicia Uvicorn. El
                embedding queda fijo en .env.
              </Text>
            </VStack>

            {error ? (
              <Banner status="error" title="Config" description={error} />
            ) : null}
            {success ? (
              <Banner status="success" title="Listo" description={success} />
            ) : null}

            {loading ? (
              <Text color="secondary">Cargando…</Text>
            ) : config ? (
              <VStack gap={5}>
                {ROLES.map((role) => {
                  const view = config.models[role.key];
                  return (
                    <VStack key={role.key} gap={2}>
                      <HStack gap={2} wrap="wrap" align="center">
                        <Text type="body">{role.label}</Text>
                        {view?.overridden ? (
                          <Badge variant="teal" label="override" />
                        ) : (
                          <Badge variant="neutral" label="default" />
                        )}
                      </HStack>
                      <Text type="supporting" color="secondary">
                        {role.description}
                        {view
                          ? ` · efectivo ahora: ${view.effective}`
                          : ""}
                      </Text>
                      <Selector
                        label={role.label}
                        isLabelHidden
                        options={options}
                        value={draft[role.key] ?? DEFAULT_VALUE}
                        onChange={(value) =>
                          setDraft((prev) => ({
                            ...prev,
                            [role.key]: value || DEFAULT_VALUE,
                          }))
                        }
                        hasClear={false}
                        isDisabled={saving}
                      />
                    </VStack>
                  );
                })}

                <VStack gap={2}>
                  <Text type="body">Embedding (solo lectura)</Text>
                  <Text type="supporting" color="secondary">
                    {config.embedding_model} — {config.embedding_model_note}
                  </Text>
                </VStack>

                <HStack gap={3} wrap="wrap">
                  <Button
                    label={saving ? "Guardando…" : "Guardar"}
                    variant="primary"
                    onClick={() => void onSave()}
                    isDisabled={saving}
                  />
                  <Button
                    label="Recargar"
                    variant="ghost"
                    onClick={() => void load()}
                    isDisabled={saving}
                  />
                </HStack>
              </VStack>
            ) : null}
          </VStack>
        </LayoutContent>
      }
    />
  );
}
