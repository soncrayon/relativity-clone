import { getGroups } from "@/features/groups/api/groups";

export const loader = async () => {
  const groups = await getGroups();
  return { groups };
};
