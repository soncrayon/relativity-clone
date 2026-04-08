import { getWorkspaces } from "@/api/workspaces";

export const loader = async () => {
  const workspaces = await getWorkspaces();
  return { workspaces };
};
