import { users } from '@/data/users';

export async function loader() {
  return { users };
}
