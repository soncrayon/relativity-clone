import { getWorkspaces } from "@/features/workspaces/api/workspaces";

export const loader = async () => {
  const workspaces = await getWorkspaces();
  return { workspaces };
};
