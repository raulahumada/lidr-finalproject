"use client";

import Link from "next/link";
import { LinkProvider } from "@astryxdesign/core/Link";
import { Theme } from "@astryxdesign/core/theme";
import { themes, defaultThemeSlug } from "../src/astryx-themes";
import { ChatSessionsProvider } from "./lib/chat-sessions-context";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <Theme theme={themes[defaultThemeSlug]} mode="dark">
      <LinkProvider component={Link}>
        <ChatSessionsProvider>{children}</ChatSessionsProvider>
      </LinkProvider>
    </Theme>
  );
}
