export interface Workspace {
  id: number;
  name: string;
  description: string | null;
  created_by_id: number | null;
  created_at: string;
}
