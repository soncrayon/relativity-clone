export interface User {
  id: string;
  name: string;
  email: string;
}

export const users: User[] = [
  {
    id: "101",
    name: "Alice Smith",
    email: "alice.smith@example.com",
  },
  {
    id: "102",
    name: "Bob Johnson",
    email: "bob.johnson@example.com",
  },
  {
    id: "103",
    name: "Charlie Brown",
    email: "charlie.brown@example.com",
  },
];
