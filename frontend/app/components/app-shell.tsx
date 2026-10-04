"use client";

import { usePathname } from "next/navigation";
import { AppShell } from "@astryxdesign/core/AppShell";
import { Icon } from "@astryxdesign/core/Icon";
import { NavIcon } from "@astryxdesign/core/NavIcon";
import {
  SideNav,
  SideNavHeading,
  SideNavItem,
  SideNavSection,
} from "@astryxdesign/core/SideNav";
import { Box, Folder, Home, Settings } from "lucide-react";

export function AppShellLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <AppShell
      contentPadding={6}
      height="fill"
      variant="elevated"
      sideNav={
        <SideNav
          aria-label="Navegación principal"
          collapsible
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
          </SideNavSection>
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
