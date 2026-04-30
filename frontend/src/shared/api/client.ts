/**
 * API client setup
 */

import axios from "axios";
import { getOrCreateClientId } from "@/shared/lib/client-id";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Create axios instance with client_id header
 */
export const apiClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Add client_id header to all requests
 */
apiClient.interceptors.request.use((config) => {
  const clientId = getOrCreateClientId();
  config.headers["X-Client-Id"] = clientId;
  return config;
});

/**
 * Health check
 */
export async function healthCheck(): Promise<boolean> {
  try {
    const response = await axios.get(`${API_URL}/health`);
    return response.data.status === "ok";
  } catch {
    return false;
  }
}
