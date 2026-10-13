"use client";

import { Suspense, useEffect, useState } from "react";
import { usePathname, useSearchParams } from "next/navigation";

import { AppShell } from "@astryxdesign/core/AppShell";
import { Icon } from "@astryxdesign/core/Icon";
import { MoreMenu } from "@astryxdesign/core/MoreMenu";
import { NavIcon } from "@astryxdesign/core/NavIcon";
import {
  SideNav,
  SideNavHeading,
  SideNavItem,
  SideNavSection,
} from "@astryxdesign/core/SideNav";
import { StatusDot } from "@astryxdesign/core/StatusDot";
import { VStack } from "@astryxdesign/core/Layout";
import {
  Box,
  Database,
  Folder,
  Home,
  MessageSquare,
  Network,
  Plus,
  Search,
  Settings,
} from "lucide-react";

import { useChatSessions } from "../lib/chat-sessions-context";
import type { SessionSummary } from "../lib/api/sessions";

function sessionLabel(item: SessionSummary): string {
  if (item.title?.trim()) return item.title.trim();
  return `Chat ${item.session_id.slice(0, 8)}`;
}

function ChatSessionNavItem({
  item,
  isSelected,
  isBusy,
  onDelete,
}: {
  item: SessionSummary;
  isSelected: boolean;
  isBusy: boolean;
  onDelete: () => void;
}) {
  const [isHovered, setIsHovered] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const showMenu = isHovered || isMenuOpen || isSelected;

  return (
    <VStack
      gap={0}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <SideNavItem
        label={sessionLabel(item)}
        icon={MessageSquare}
        href={`/answer?session=${encodeURIComponent(item.session_id)}`}
        isSelected={isSelected}
        endContent={
          showMenu ? (
            <MoreMenu
              size="sm"
              label="Opciones de la sesión"
              alignment="end"
              onOpenChange={setIsMenuOpen}
              items={[{ label: "Eliminar", onClick: onDelete }]}
            />
          ) : isBusy ? (
            <StatusDot
              variant="accent"
              label="Corrida en curso"
              isPulsing
              tooltip="Hay una corrida agentic en curso"
            />
          ) : item.turn_count > 0 ? (
            <StatusDot
              variant="neutral"
              label={`${item.turn_count} turnos`}
              tooltip={`${item.turn_count} turno${item.turn_count === 1 ? "" : "s"}`}
            />
          ) : null
        }
      />
    </VStack>
  );
}

function ChatSessionsNav() {
  const searchParams = useSearchParams();
  const activeSessionId = searchParams.get("session");
  const {
    sessions,
    sessionsReady,
    busySessionIds,
    refreshSessions,
    createSessionAndOpen,
    deleteSession,
    openSession,
  } = useChatSessions();

  useEffect(() => {
    void refreshSessions().catch(() => {
      /* answer page also boots */
    });
  }, [refreshSessions]);

  return (
    <SideNavSection title="Conversaciones">
      <SideNavItem
        label="Nueva conversación"
        icon={Plus}
        isDisabled={!sessionsReady}
        onClick={() => {
          void createSessionAndOpen();
        }}
      />
      {sessions.map((item) => (
        <ChatSessionNavItem
          key={item.session_id}
          item={item}
          isSelected={item.session_id === activeSessionId}
          isBusy={busySessionIds.has(item.session_id)}
          onDelete={() => {
            void (async () => {
              const wasActive = item.session_id === activeSessionId;
              const list = await deleteSession(item.session_id);
              if (!wasActive) return;
              if (list.length === 0) {
                await createSessionAndOpen();
                return;
              }
              openSession(list[0].session_id);
            })();
          }}
        />
      ))}
    </SideNavSection>
  );
}

export function AppShellLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const onChat = pathname.startsWith("/answer");
  // autoSaveId reads localStorage on the client; enable only after mount
  // so SSR and the first client paint share defaultWidth (no hydration mismatch).
  const [sideNavPersistReady, setSideNavPersistReady] = useState(false);
  useEffect(() => {
    setSideNavPersistReady(true);
  }, []);

  return (
    <AppShell
      contentPadding={onChat ? 0 : 6}
      height="fill"
      variant="elevated"
      sideNav={
        <SideNav
          aria-label="Navegación principal"
          collapsible
          resizable={{
            defaultWidth: 280,
            minWidth: 220,
            maxWidth: 400,
            ...(sideNavPersistReady
              ? { autoSaveId: "entrega-lidr-sidenav" }
              : {}),
          }}
          header={
            <SideNavHeading
              icon={<NavIcon icon={<Icon icon={Box} size="sm" />} />}
              heading="Entrega LiDR"
              headingHref="/"
            />
          }
        >
          <SideNavSection title="Principal" isHeaderHidden>
            <SideNavItem
              label="Inicio"
              icon={Home}
              href="/"
              isSelected={pathname === "/"}
            />
            <SideNavItem
              label="Items"
              icon={Folder}
              href="/items"
              isSelected={pathname.startsWith("/items")}
            />
            <SideNavItem
              label="Chat"
              icon={MessageSquare}
              href="/answer"
              isSelected={onChat}
            />
            <SideNavItem
              label="Agentes"
              icon={Network}
              href="/agents"
              isSelected={pathname.startsWith("/agents")}
            />
            <SideNavItem
              label="Búsqueda"
              icon={Search}
              href="/search"
              isSelected={pathname.startsWith("/search")}
            />
            <SideNavItem
              label="Ingesta"
              icon={Database}
              href="/ingest"
              isSelected={pathname.startsWith("/ingest")}
            />
          </SideNavSection>

          {onChat ? (
            <Suspense fallback={null}>
              <ChatSessionsNav />
            </Suspense>
          ) : null}

          <SideNavSection title="Sistema">
            <SideNavItem
              label="Ajustes"
              icon={Settings}
              href="/settings"
              isSelected={pathname.startsWith("/settings")}
            />
          </SideNavSection>
        </SideNav>
      }
    >
      {children}
    </AppShell>
  );
}
