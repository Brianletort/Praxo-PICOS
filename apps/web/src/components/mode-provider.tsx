"use client";

import { ModeContext, useModeState } from "@/lib/use-mode";

export function ModeProvider({ children }: { children: React.ReactNode }) {
  const modeValue = useModeState();

  return (
    <ModeContext.Provider value={modeValue}>{children}</ModeContext.Provider>
  );
}
