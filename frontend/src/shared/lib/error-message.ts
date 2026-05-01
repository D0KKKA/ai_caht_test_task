type ErrorWithResponse = {
  response?: {
    data?: {
      detail?: string;
      message?: string;
    } | string;
  };
};

export function getErrorMessage(
  error: unknown,
  fallback = "Произошла ошибка. Попробуйте ещё раз."
): string {
  if (error && typeof error === "object" && "response" in error) {
    const response = (error as ErrorWithResponse).response;
    const data = response?.data;

    if (typeof data === "string" && data.trim()) {
      return data;
    }

    if (data && typeof data === "object") {
      if (typeof data.detail === "string" && data.detail.trim()) {
        return data.detail;
      }

      if (typeof data.message === "string" && data.message.trim()) {
        return data.message;
      }
    }
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }

  return fallback;
}
