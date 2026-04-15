import { apiClient } from "@/lib/api-client";
import type { Document } from "@/features/documents/types";

const base = (workspaceId: number) => `/workspaces/${workspaceId}/documents`;

export const getDocuments = (workspaceId: number): Promise<Document[]> =>
  apiClient.get<Document[]>(`${base(workspaceId)}/`);

export const uploadDocument = (workspaceId: number, file: File): Promise<Document> => {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient.upload<Document>(`${base(workspaceId)}/upload`, formData);
};

export const processDocument = (workspaceId: number, docId: number): Promise<Document> =>
  apiClient.post<Document>(`${base(workspaceId)}/${docId}/process`);

export const chunkDocument = (workspaceId: number, docId: number): Promise<unknown> =>
  apiClient.post(`${base(workspaceId)}/${docId}/chunk`);
