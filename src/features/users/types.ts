export interface User {
  id: number;
  name: string;
  email: string;
  role: "admin" | "reviewer" | "viewer";
  is_active: boolean;
  created_at: string;
}
