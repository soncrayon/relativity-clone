import { apiClient } from "@/lib/api-client";
import type { Group } from "@/data/groups";

export const getGroups = (): Promise<Group[]> => apiClient.get<Group[]>("/groups/");

export const getGroup = (id: number): Promise<Group> => apiClient.get<Group>(`/groups/${id}`);
