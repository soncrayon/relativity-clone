import { apiClient } from "@/lib/api-client";
import type { Workspace } from "@/features/workspaces/types";

export const getWorkspaces = (): Promise<Workspace[]> => apiClient.get<Workspace[]>("/workspaces/");

export const getWorkspace = (id: number): Promise<Workspace> =>
  apiClient.get<Workspace>(`/workspaces/${id}`);

export const deleteWorkspace = (id: number): Promise<void> => apiClient.delete(`/workspaces/${id}`);
