import { apiClient } from "@/lib/api-client";
import type { User } from "@/features/users/types";

export const getUsers = (): Promise<User[]> => apiClient.get<User[]>("/users/");

export const getUser = (id: number): Promise<User> => apiClient.get<User>(`/users/${id}`);
