"use client";

import { useEffect } from "react";
import { getOrCreateClientId } from "@/shared/lib/client-id";

export function ClientInitializer() {
  useEffect(() => {
    // Initialize client ID as soon as possible
    getOrCreateClientId();
  }, []);

  return null;
}
