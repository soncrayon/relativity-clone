import { workspaces } from '@/data/workspaces';

export async function loader() {
  return { workspaces };
}
