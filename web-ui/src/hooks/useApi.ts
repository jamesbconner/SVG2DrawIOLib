"use client";

import { useCallback, useState } from "react";
import { ApiError } from "@/lib/api";

interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiReturn<T, Args extends unknown[]> extends ApiState<T> {
  execute: (...args: Args) => Promise<T | null>;
  reset: () => void;
}

/**
 * Generic hook for managing API call state (loading, error, data).
 *
 * @param fn - The async API function to call.
 * @returns State and an `execute` function that invokes the API call.
 */
export function useApi<T, Args extends unknown[]>(
  fn: (...args: Args) => Promise<T>,
): UseApiReturn<T, Args> {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async (...args: Args): Promise<T | null> => {
      setState({ data: null, loading: true, error: null });
      try {
        const result = await fn(...args);
        setState({ data: result, loading: false, error: null });
        return result;
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.detail
            : err instanceof Error
              ? err.message
              : "An unexpected error occurred";
        setState({ data: null, loading: false, error: message });
        return null;
      }
    },
    [fn],
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return { ...state, execute, reset };
}
