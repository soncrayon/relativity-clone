import { getUsers } from "@/features/users/api/users";

export const loader = async () => {
  const users = await getUsers();
  return { users };
};
