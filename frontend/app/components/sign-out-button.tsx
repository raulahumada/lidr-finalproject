"use client";

import { Button } from "@astryxdesign/core/Button";

import { signOutAction } from "./sign-out-action";


export function SignOutButton() {
  return (
    <form action={signOutAction}>
      <Button type="submit" variant="ghost" size="sm" label="Salir" width="100%" />
    </form>
  );
}
