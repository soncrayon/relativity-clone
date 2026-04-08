import { getGroups } from "@/api/groups";

export const loader = async () => {
  const groups = await getGroups();
  return { groups };
};
