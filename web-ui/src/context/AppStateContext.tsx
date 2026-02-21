"use client";

import React, { createContext, useContext, useState } from "react";

interface AppState {
  sharedLibraryFile: File | null;
  sharedIconNames: string[];
  globalError: string | null;
}

interface AppStateContextValue extends AppState {
  setSharedLibraryFile: (file: File | null) => void;
  setSharedIconNames: (names: string[]) => void;
  setGlobalError: (error: string | null) => void;
}

const AppStateContext = createContext<AppStateContextValue>({
  sharedLibraryFile: null,
  sharedIconNames: [],
  globalError: null,
  setSharedLibraryFile: () => {},
  setSharedIconNames: () => {},
  setGlobalError: () => {},
});

export function AppStateProvider({ children }: { children: React.ReactNode }) {
  const [sharedLibraryFile, setSharedLibraryFile] = useState<File | null>(null);
  const [sharedIconNames, setSharedIconNames] = useState<string[]>([]);
  const [globalError, setGlobalError] = useState<string | null>(null);

  return (
    <AppStateContext.Provider
      value={{
        sharedLibraryFile,
        sharedIconNames,
        globalError,
        setSharedLibraryFile,
        setSharedIconNames,
        setGlobalError,
      }}
    >
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  return useContext(AppStateContext);
}
