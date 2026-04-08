import { getUsers } from "@/api/users";

export const loader = async () => {
  const users = await getUsers();
  return { users };
};
