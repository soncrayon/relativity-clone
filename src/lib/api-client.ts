/**
 * Single configured API client instance.
 * Only files in src/api/ should import from here — use the typed
 * fetcher functions in src/api/*.ts everywhere else.
 * (Enforced by the no-restricted-imports rule in .oxlintrc.json)
 */
const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

const request = async <T>(method: HttpMethod, path: string, body?: unknown): Promise<T> => {
  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    ...(body !== undefined && { body: JSON.stringify(body) }),
  });

  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText} (${path})`);
  }

  // 204 No Content — delete endpoints return nothing
  if (response.status === 204) return undefined as T;

  return response.json() as Promise<T>;
};

// File upload — lets the browser set multipart/form-data with the correct boundary.
// Do NOT set Content-Type manually here; it must be omitted for multipart uploads.
const uploadRequest = async <T>(path: string, formData: FormData): Promise<T> => {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText} (${path})`);
  }

  return response.json() as Promise<T>;
};

export const apiClient = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  delete: <T>(path: string) => request<T>("DELETE", path),
  upload: <T>(path: string, formData: FormData) => uploadRequest<T>(path, formData),
};
