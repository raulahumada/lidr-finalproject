"use client";

/**
 * Client context for the multi-session sidebar on /answer.
 * Lists/creates/deletes sessions via same-origin BFF clients.
 *
 * || Contexto cliente del sidebar multi-sesión en /answer.
 */
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

import {
  createAnswerSession,
  deleteAnswerSession,
  listAnswerSessions,
  type SessionSummary,
} from "./api/sessions";

type ChatSessionsContextValue = {
  sessions: SessionSummary[];
  sessionsReady: boolean;
  busySessionIds: ReadonlySet<string>;
  refreshSessions: () => Promise<SessionSummary[]>;
  markBusy: (sessionId: string, busy: boolean) => void;
  createSessionAndOpen: () => Promise<string>;
  deleteSession: (sessionId: string) => Promise<SessionSummary[]>;
  openSession: (sessionId: string) => void;
};

const ChatSessionsContext = createContext<ChatSessionsContextValue | null>(
  null,
);

export function ChatSessionsProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [sessionsReady, setSessionsReady] = useState(false);
  const [busySessionIds, setBusySessionIds] = useState<Set<string>>(
    () => new Set(),
  );

  const refreshSessions = useCallback(async () => {
    const list = await listAnswerSessions();
    setSessions(list);
    setSessionsReady(true);
    return list;
  }, []);

  const markBusy = useCallback((sessionId: string, busy: boolean) => {
    setBusySessionIds((prev) => {
      const next = new Set(prev);
      if (busy) next.add(sessionId);
      else next.delete(sessionId);
      return next;
    });
  }, []);

  const openSession = useCallback(
    (sessionId: string) => {
      router.push(`/answer?session=${encodeURIComponent(sessionId)}`);
    },
    [router],
  );

  const createSessionAndOpen = useCallback(async () => {
    const created = await createAnswerSession();
    await refreshSessions();
    openSession(created.session_id);
    return created.session_id;
  }, [openSession, refreshSessions]);

  const deleteSession = useCallback(
    async (sessionId: string) => {
      await deleteAnswerSession(sessionId);
      markBusy(sessionId, false);
      return refreshSessions();
    },
    [markBusy, refreshSessions],
  );

  const value = useMemo(
    () => ({
      sessions,
      sessionsReady,
      busySessionIds,
      refreshSessions,
      markBusy,
      createSessionAndOpen,
      deleteSession,
      openSession,
    }),
    [
      sessions,
      sessionsReady,
      busySessionIds,
      refreshSessions,
      markBusy,
      createSessionAndOpen,
      deleteSession,
      openSession,
    ],
  );

  return (
    <ChatSessionsContext.Provider value={value}>
      {children}
    </ChatSessionsContext.Provider>
  );
}

export function useChatSessions(): ChatSessionsContextValue {
  const ctx = useContext(ChatSessionsContext);
  if (!ctx) {
    throw new Error("useChatSessions must be used within ChatSessionsProvider");
  }
  return ctx;
}
