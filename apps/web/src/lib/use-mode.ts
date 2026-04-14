"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";

type Mode = "simple" | "advanced";

interface ModeContextValue {
  mode: Mode;
  isAdvanced: boolean;
  toggleMode: () => void;
  setMode: (m: Mode) => void;
}

const STORAGE_KEY = "picos-ui-mode";

export const ModeContext = createContext<ModeContextValue>({
  mode: "simple",
  isAdvanced: false,
  toggleMode: () => {},
  setMode: () => {},
});

export function useMode(): ModeContextValue {
  return useContext(ModeContext);
}

export function useModeState(): ModeContextValue {
  const [mode, setModeState] = useState<Mode>("simple");

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "advanced" || stored === "simple") {
      setModeState(stored);
    }
  }, []);

  const setMode = useCallback((m: Mode) => {
    setModeState(m);
    localStorage.setItem(STORAGE_KEY, m);
  }, []);

  const toggleMode = useCallback(() => {
    setMode(mode === "simple" ? "advanced" : "simple");
  }, [mode, setMode]);

  return {
    mode,
    isAdvanced: mode === "advanced",
    toggleMode,
    setMode,
  };
}
