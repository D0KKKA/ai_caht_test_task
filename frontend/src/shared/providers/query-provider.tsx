"use client";

/**
 * TanStack Query provider
 */

import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/shared/lib/query-client";
import { ClientInitializer } from "./client-initializer";
import { ReactNode } from "react";

interface QueryProviderProps {
  children: ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <ClientInitializer />
      {children}
    </QueryClientProvider>
  );
}
