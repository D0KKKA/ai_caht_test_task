import axios, { AxiosHeaders } from "axios";
import { getOrCreateClientId } from "@/shared/lib/client-id";
import { API_BASE_PATH } from "@/shared/lib/api";

export const apiClient = axios.create({
  baseURL: API_BASE_PATH,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const clientId = getOrCreateClientId();

  if (clientId) {
    config.headers = AxiosHeaders.from(config.headers);
    config.headers.set("X-Client-Id", clientId);
  }

  return config;
});
