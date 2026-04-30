"use client";

import { ReactNode } from "react";
import { ThemeProvider } from "next-themes";
import { QueryProvider } from "./query-provider";

interface RootProviderProps {
  children: ReactNode;
}

export function RootProvider({ children }: RootProviderProps) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <QueryProvider>{children}</QueryProvider>
    </ThemeProvider>
  );
}
